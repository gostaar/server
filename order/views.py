from django.dispatch import receiver
from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializer import CustomerOrderSerializer, OrderActionSerializer, OrderCommentSerializer
from .models import OrderAction, OrderComment, User, CustomerOrder, CustomerBilling, CustomerDelivery, CustomerContact,Attachment, OrderLine, CustomerFinancial
from companies.models import AlertAddress, Enterprise, Establishment
from django.core.files.base import ContentFile
from django.db import models
import base64
import os
from uuid_extensions import uuid7,uuid7str
import jwt

# Méthode de création du token JWT
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role
        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# Méthode de création / mise à jour du formulaire de bon de commande
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createOrder(request):
    if request.method == "POST":
        formData = request.data
        # User
        currentUser = User.objects.get(username = formData.get("user"))
        # Billing 
        billing = formData.get("billing")
        newBilling = saveBilling(billing)
        formData["billing"]["id"] = newBilling.id if newBilling != None else ""       
        # Delivery
        delivery = formData.get("delivery")
        newDelivery = saveDelivery(delivery)
        formData["delivery"]["id"] = newDelivery.id if newDelivery != None else ""
        # Financial
        financial = formData.get("financial")
        newFinancial = saveFinancial(financial)
        formData["financial"]["id"] = newFinancial.id if newFinancial != None else ""
        # Contacts creation
        contact = formData.get("contact")
        newContacts = []
        if len(contact) > 0 and f"{contact[0].get("firstName")}{contact[0].get("lastName")}" != '':
            for c in contact:
                newContact = saveContact(c)
                newContacts.append(newContact)
        # CustomerOrder
        newOrder = CustomerOrder.objects.get(pk=formData.get("id")) if formData.get("id") != "" else CustomerOrder(
            id = uuid7(),
            status=CustomerOrder.CustomerStatus.CREATED,
            user = currentUser,
        )
        newOrder.customer_comment = formData.get("orderComment")
        if newBilling != None:
            newOrder.billing = newBilling
        if newDelivery != None:
            newOrder.delivery = newDelivery
        newOrder.save()
        if formData.get("id") != newOrder.id:
            formData["id"]= newOrder.id
        # Assign contacts to Order
        if len(newContacts) != 0:
            newOrder.contacts.set(newContacts)
            for i in range(len(contact)):
                formData["contact"][i]["id"] = newContacts[i].id
        # OrderLines
        orderContent = formData.get("orderContent")
        orderContent = list(filter(lambda l: l.get("description") != '', list(orderContent)))
        newOrderLines = []
        for line in orderContent:
            newLine = saveOrderLine(line, newOrder)
            newOrderLines.append(newLine)
        if len(newOrderLines) != 0:
            for i in range(len((orderContent))):
                formData["orderContent"][i]["id"] = newOrderLines[i].id
        return Response(formData, status=status.HTTP_201_CREATED)
    return Response({'errors':[]}, status=status.HTTP_400_BAD_REQUEST)

# Méthode pour obtenir l'id de l'utilisateur qui émet la requête en utilisant son token
def getUserId(request):
    token = request.META['HTTP_AUTHORIZATION'][7:]
    return jwt.decode(token, os.environ.get('SECRET_KEY'), ['HS256']).get("user_id")

# Méthode pour obtenir les commandes (tous si ADMIN sinon ceux liés à l'utilisateur (commercial)) (en models)
def getOrdersModels(request):
    token = request.META['HTTP_AUTHORIZATION'][7:]
    userId = jwt.decode(token, os.environ.get('SECRET_KEY'), ['HS256']).get("user_id")
    role = jwt.decode(token, os.environ.get('SECRET_KEY'), ['HS256']).get("role")
    orders = CustomerOrder.objects.all() if role == "ADMIN" else CustomerOrder.objects.filter(user_id=userId)
    return orders

# Méthode utilisant la méthode ci-dessus et sérialisant les données
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAllOrders(request):
    orders = getOrdersModels(request)
    serializer = CustomerOrderSerializer(orders, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Méthode retournant la commande à partir de l'id et si n'existe pas une erreur 404
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getOrderById(request, pk):
    try:
        order = CustomerOrder.objects.get(pk=pk)
    except CustomerOrder.DoesNotExist:
        return Response({"message":"Le bon de commande n'existe pas"}, status=status.HTTP_404_NOT_FOUND)
    serializer = CustomerOrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Méthode retournant les différents statuts possibles pour les commandes
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAllOrderStatus(request):
    return Response(CustomerOrder.CustomerStatus.choices, status=status.HTTP_200_OK)

# Méthode permettant de supprimer une personne de contact
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteContact(request, pk:str):
    if pk == None:
        return Response({'message':"Aucune personne de contact sélectionnée"}, status=status.HTTP_400_BAD_REQUEST)
    contact = CustomerContact.objects.get(pk=pk)
    order = CustomerOrder.objects.filter(contacts__in=[contact.id]).first()
    contact_name = contact.__str__()
    contact.delete()
    OrderAction.objects.create(id=uuid7(),description=" a supprimé une personne de contact le ", order=order, user_id=getUserId(request), additionalContext=contact_name)
    return Response({"message":"Personne de contact supprimée"}, status=status.HTTP_200_OK)

# Méthode permettant de supprimer un ligne de commande (OrderLine)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteOrderLine(request, pk:str):
    if pk == None:
        return Response({'message':"Aucune ligne de commande sélectionnée"}, status=status.HTTP_400_BAD_REQUEST)
    orderLine = OrderLine.objects.get(pk=pk)
    orderLine.delete()
    return Response({"message":"Ligne de commande supprimée"}, status=status.HTTP_200_OK)

# Méthode pour supprimer 1 à plusieurs Attachment(s)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deleteAttachements(request):
    
    filesToDelete = list(request.data.get("files"))
    order = Attachment.objects.get(pk=filesToDelete[0]).order
    for file in filesToDelete:
        attachment = Attachment.objects.get(pk=file)
        filename = attachment.filename
        attachment.delete()
        OrderAction.objects.create(id=uuid7(),description=" a mis supprimé une pièce jointe le ", order=order, user_id=getUserId(request), additionalContext=filename)
    return Response({"message":"Pièce jointe supprimée" if len(filesToDelete) == 1 else "Pièces jointes supprimées"}, status=status.HTTP_200_OK)

# Méthode pour upload un fichier
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def uploadFile(request):
    if request.method == "POST":
        formData= request.data
        order = CustomerOrder.objects.get(pk=formData.get("order"))
        file = request.data.get("file")
        format, imgstr = file.get("content").split(';base64,')
        ext = format.split('/')[-1]
        data = ContentFile(base64.b64decode(imgstr), name=f'{uuid7str()}.{ext}')
        newFile =Attachment(
            id= uuid7(),
            order = order,
            type = file.get("type"),
            mime = format[5:],
            size = 1,
            url = "",
            file = data,
            filename=file.get("name")
        )
        newFile.save()
        newFile.url = newFile.file.url
        newFile.size = newFile.file.size
        newFile.save()
        id = newFile.id
        if newFile.type == "signature":
            order.status = CustomerOrder.CustomerStatus.BOARDING
            order.save()
        return Response({"id": id, "size":newFile.size}, status=status.HTTP_201_CREATED)
    return Response({'errors':[]}, status=status.HTTP_400_BAD_REQUEST)

# Méthode pour supprimer une signature
#TODO: implémentation de la suppression de la signature
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deleteAttachement(request):
    fileToDelete = list(request.data.get("files"))
    order = Attachment.objects.get(pk=fileToDelete[0]).order
    for file in fileToDelete:
        attachment = Attachment.objects.get(pk=file)
        filename = attachment.filename
        attachment.delete()
        OrderAction.objects.create(id=uuid7(),description=" a mis supprimé une pièce jointe le ", order=order, user_id=getUserId(request), additionalContext=filename)
    return Response({"message":"Pièce jointe supprimée" if len(fileToDelete) == 1 else "Pièces jointes supprimées"}, status=status.HTTP_200_OK)

# Méthode pour obtenir les différents types de fichier
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAllFileTypes(request):
    return Response(Attachment.AttachmentType.choices, status=status.HTTP_200_OK)

# Méthode pour changer le type de fichier à un fichier spécifique
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def changeFileType(request,pk):
    type = request.data.get("type")
    file = Attachment.objects.get(pk=pk)
    file.type = type
    file.save()
    return Response({'message':"Type changé"}, status=status.HTTP_200_OK)

# Méthode pour abandonner une commande
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def abandonOrder(request, pk):
    if pk == None:
        return Response({'message':"Aucun bon de commande sélectionné"}, status=status.HTTP_400_BAD_REQUEST)
    order = CustomerOrder.objects.get(pk = pk)
    order.status = CustomerOrder.CustomerStatus.ABANDONED
    order.save()
    return Response({'message':"Le bon de commande a été abandonné"}, status=status.HTTP_200_OK)

# Méthode pour ajouter / modifier la partie facturation du formulaire de commande
def saveBilling(billing):
    newBilling = None
    if any([billing.get(k) !="" for k in billing if k != 'id']):
        if billing.get("id") != "":
            newBilling = CustomerBilling.objects.get(pk=billing.get("id"))
            newBilling.id = billing.get("id")
            newBilling.name = billing.get("name")
            newBilling.company_number = billing.get("companyNumber")
            newBilling.address1 = billing.get("address1")
            newBilling.address2 = billing.get("address2")
            newBilling.zip = billing.get("zip")
            newBilling.city = billing.get("city")
            newBilling.country = billing.get("country")
            newBilling.phone = billing.get("phone")
            newBilling.mail = billing.get("mail")
        else:
            newBilling = CustomerBilling(
                id= uuid7(),
                name=billing.get("name"),
                company_number = billing.get("companyNumber"),
                address1 = billing.get("address1"),
                address2 = billing.get("address2"),
                zip = billing.get("zip"),
                city = billing.get("city"),
                country = billing.get("country"),
                phone = billing.get("phone"),
                mail = billing.get("mail")
            )
        newBilling.save()
    return newBilling

# Méthode pour ajouter / modifier la partie livraison du formulaire de commande
def saveDelivery(delivery):
    newDelivery = None
    if any([delivery.get(k) !="" for k in delivery if k not in ['id','identicalBilling', 'country']]):
        if delivery.get("id") != "":
            newDelivery = CustomerDelivery.objects.get(pk=delivery.get("id"))
            newDelivery.id = delivery.get("id")
            newDelivery.name = delivery.get("name")
            newDelivery.address1 = delivery.get("address1")
            newDelivery.address2 = delivery.get("address2")
            newDelivery.zip = delivery.get("zip")
            newDelivery.city = delivery.get("city")
            newDelivery.country = delivery.get("country")
            newDelivery.phone = delivery.get("phone")
            newDelivery.mail = delivery.get("mail")
        else:
            newDelivery = CustomerDelivery(
                id= uuid7(),
                name=delivery.get("name"),
                address1 = delivery.get("address1"),
                address2 = delivery.get("address2"),
                zip = delivery.get("zip"),
                city = delivery.get("city"),
                country = delivery.get("country"),
                phone = delivery.get("phone"),
                mail = delivery.get("mail")
            )
        newDelivery.save()
    return newDelivery
    
# Méthode pour ajouter / modifier un financement
def saveFinancial(financial):
    newFinancial = None
    if any([financial.get(k) !="" for k in financial if k not in ['id']]):
        if financial.get('id') != "":
            newFinancial = CustomerFinancial.objects.get(pk=financial.get('id'))
            newFinancial.id = financial.get("id")
            newFinancial.type = financial.get("type")
            newFinancial.comment = financial.get("comment")
            newFinancial.bankDuration = financial.get("bankDuration")
        else:
            newFinancial = CustomerFinancial(
                id= uuid7(),
                type= financial.get("type"),
                comment= financial.get("comment"),
                bankDuration= financial.get("bankDuration")
            )
        newFinancial.save()
    return newFinancial

# Méthode pour ajouter / modifier une personne de contact dans la partie contact du formulaire de commande
def saveContact(contact):
    newContact = None

    if contact.get("id") != "":
            newContact = CustomerContact.objects.get(pk=contact.get("id"))
            newContact.id = contact.get("id")
            newContact.first_name = contact.get("firstName")
            newContact.last_name = contact.get("lastName")
            newContact.phone = contact.get("phone")
            newContact.mail = contact.get("mail")
    else:
        newContact = CustomerContact(
            id= uuid7(),
            first_name=contact.get("firstName"),
            last_name = contact.get("lastName"),
            phone = contact.get("phone"),
            mail = contact.get("mail")
        )
    newContact.save()
    return newContact

# Méthode pour ajouter / modifier une ligne de commande dans la partie order du formulaire de commande
def saveOrderLine(line, order:CustomerOrder):
    newOrderLine = None
    if line.get("id") != "":
        newOrderLine = OrderLine.objects.get(pk=line.get("id"))
        newOrderLine.id = line.get("id")
        newOrderLine.description = line.get("description")
        newOrderLine.quantity = line.get("quantity")
        newOrderLine.price = line.get("price")
        newOrderLine.order = order
    else:
        newOrderLine = OrderLine(
            id= uuid7(),
            description = line.get("description"),
            quantity = line.get("quantity"),
            price = line.get("price"),
            order = order
        )
    newOrderLine.save()
    return newOrderLine

# Méthode de vérification d'adresse et d'alerte possible pour un bon de commande
def compareAddressPlusAlert(order:CustomerOrder) ->bool:
    enterpriseNumber = order.billing.company_number
    enterprise = Enterprise.objects.get(pk=enterpriseNumber)
    if enterprise.street == None:
        esta = Establishment.objects.filter(enterprise_id=enterpriseNumber).first()
        last_alert = AlertAddress.objects.filter(establishmentNumber_id=esta.establishmentNumber).first()
        if last_alert == None:
            return True
        enterprise.street = esta.street
        enterprise.city = esta.city
        enterprise.zip = esta.zip
        enterprise.street = esta.street
        enterprise.number = esta.number
        enterprise.box = esta.box
        enterprise.extraAddressInfo = esta.extraAddressInfo
        enterprise.country = esta.country
    else:
        last_alert = AlertAddress.objects.filter(enterpriseNumber_id=order.billing.company_number).first()
        if last_alert == None:
            return True
    address1Fields = ["street", "number", "box"]
    if order.billing.address1 != " ".join([enterprise.__dict__.get(field) if enterprise.__dict__.get(field) is not None else '' for field in address1Fields]):
        return False
    if (order.billing.address2 or "") != (enterprise.extraAddressInfo or ""):
        return False
    if order.billing.zip != enterprise.zip:
        return False
    if order.billing.city != enterprise.city:
        return False
    if order.billing.country != enterprise.country:
        return False
    return True

# Méthode permettant d'obtenir la liste d'ids des bons de commandes en alerte
@api_view(['GET'])
@permission_classes([IsAuthenticated])    
def getAlerts(request):
    orders = getOrdersModels(request)
    response = []
    for order in orders:
        if len(order.billing.company_number) not in [9,10]:
            continue
        if not compareAddressPlusAlert(order):
                response.append(order.id)
    return Response(response, status=status.HTTP_200_OK)

# Méthode de mise à jour du bon de commande (depuis le listing > details)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def updateOrder(request, pk):
    formData = dict(request.data)
    order = CustomerOrder.objects.get(pk=pk)
    userId = getUserId(request)
    if formData.get("status") != None:
        changes =[order.get_status_display()]
        order.status = formData.get("status")
        changes.append(order.get_status_display())
        OrderAction.objects.create(id=uuid7(),description=f" a mis à jour le statut de {" à ".join(changes)} le ", order_id=pk, user_id=userId)
    elif formData.get("billing") != None:
        billing = CustomerBilling.objects.get(pk=formData.get("billing").get("id"))
        enterprise = Enterprise.objects.get(pk=formData.get("billing").get("company_number"))
        if enterprise.street == None:
            esta = Establishment.objects.filter(enterprise_id=enterprise.enterpriseNumber).first()
            enterprise.street = esta.street
            enterprise.city = esta.city
            enterprise.zip = esta.zip
            enterprise.street = esta.street
            enterprise.number = esta.number
            enterprise.box = esta.box
            enterprise.extraAddressInfo = esta.extraAddressInfo
            enterprise.country = esta.country
        billing.zip = enterprise.zip
        billing.city = enterprise.city
        billing.country = enterprise.country
        address1Fields = ["street", "number", "box"]
        billing.address1 = " ".join([enterprise.__dict__.get(field) if enterprise.__dict__.get(field) is not None else '' for field in address1Fields])
        billing.address2 = enterprise.extraAddressInfo
        billing.save()
        OrderAction.objects.create(id=uuid7(),description=" a mis à jour l'adresse de facturation le ", order_id=pk, user_id=userId)
    elif formData.get("contacts") != None:
        newContact = list(formData.get("contacts"))[0]
        savedContact = CustomerContact.objects.create(
            id = uuid7(),
            first_name = newContact.get("first_name"),
            last_name = newContact.get("last_name"),
            mail = newContact.get("mail"),
            phone = newContact.get("phone")
        )
        order.contacts.add(savedContact)
        OrderAction.objects.create(id=uuid7(),description=" a ajouté une personne de contact le ", order_id=pk, user_id=userId, additionalContext=savedContact.__str__())
    elif formData.get('order_comments') != None:
        newComment = list(formData.get("order_comments"))[0]
        OrderComment.objects.create(
            id = uuid7(),
            description = newComment.get("description"),
            order_id=pk,
            user_id = userId
        )
        OrderAction.objects.create(id=uuid7(),description=" a ajouté un commentaire le ", order_id=pk, user_id=userId, additionalContext=newComment.get("description"))
    elif formData.get('order_lines') != None:
        newLine = list(formData.get("order_lines"))[0]
        savedLine = OrderLine.objects.create(
            id = uuid7(),
            quantity = newLine.get("quantity"),
            description = newLine.get("description"),
            price = newLine.get("price"),
            order_id=pk
        )
        OrderAction.objects.create(id=uuid7(),description=" a ajouté une ligne de commande le ", order_id=pk, user_id=userId, additionalContext=savedLine.__str__())
    elif formData.get("attachment_files") != None:
        file = list(formData.get("attachment_files"))[0]
        format, imgstr = file.get("content").split(';base64,')
        ext = format.split('/')[-1]
        data = ContentFile(base64.b64decode(imgstr), name=f'{uuid7str()}.{ext}')
        newFile =Attachment(
            id= uuid7(),
            order = order,
            type = file.get("type"),
            mime = format[5:],
            size = 1,
            url = "",
            file = data,
            filename=file.get("name")
        )
        newFile.save()
        newFile.url = newFile.file.url
        newFile.size = newFile.file.size
        print(newFile.url)
        newFile.save()
        OrderAction.objects.create(id=uuid7(),description=" a ajouté une pièce jointe le ", order_id=pk, user_id=userId, additionalContext=newFile.filename)
    order.save()
    serializer = CustomerOrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Méthode pour obtenir l'historique d'actions (détails)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getOrderHistory(request, pk):
    history = OrderAction.objects.filter(order__id=pk).order_by('-created_at')
    serializer = OrderActionSerializer(history, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Supprime le fichier du Filesystem quand l'objet AttachmentFile correspondant est supprimé
@receiver(models.signals.post_delete, sender=Attachment)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
