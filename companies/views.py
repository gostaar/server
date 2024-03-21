from django.db import connection
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
import shutil

from .serializers import EnterpriseSerializer, EstablishmentSerializer
from .forms import FileForm
from server.settings import MEDIA_ROOT
import os
import csv
import time
from .models import Enterprise, Establishment
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Méthode pour la page d'import du fichier d'entreprises
@csrf_protect
def index(request):
    form = FileForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        handle_uploaded_file(form.cleaned_data.get("file"))
        return render(request, "companies/index.html", {"form":form, "message":"Le script a terminé"})
    return render(request, "companies/index.html", {"form":form})
    
# Méthode utilisant du fichier pour le script (Entreprises, établissements, adresses et dénominations)
def handle_uploaded_file(f, deletePrevious = False):
    files = []
    BULK_SIZE = 1000
    timeDict = dict()
    
    if deletePrevious: # Si l'argument est mis à True il supprimera le contenu des tables companies_... et les fichiers csv restants
        Enterprise.truncate()
        print("Fin suppression des entreprises")
        files = [f for f in os.listdir(f"{MEDIA_ROOT}") if f.endswith(".csv")]
        if len(files) == 9: 
            for file in files:
                os.remove(f"{MEDIA_ROOT}{os.sep}{file}")
            files.clear()

    start = time.time()
    if len(files) == 0:
        newPath = f"{MEDIA_ROOT}{os.sep}data.zip"
        with open(newPath, "wb+") as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        print("Etape effectuée - Fichier .zip copié")
        shutil.unpack_archive(newPath, MEDIA_ROOT)
        print("Etape effectuée - Fichier dézippé")
        os.remove(newPath)
        print("Etape effectuée - Suppression du fichier .zip")
    print("Début étape - Mise en DB")
    
    #Entreprises
    with open(f"{MEDIA_ROOT}{os.sep}enterprise.csv", newline='', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        tempEnterprises = []
        startEnterprise = time.time()
        for row in reader:
            newEntreprise = dict(
                enterpriseNumber = int(row["EnterpriseNumber"].replace(".", "")),
                active = True if row["Status"] == "AC" else False,
            )
            count += 1
            tempEnterprises.append(newEntreprise)
            if count % BULK_SIZE == 0:
                addEntreprise(tempEnterprises)
                tempEnterprises.clear()
        if len(tempEnterprises) > 0:
            addEntreprise(tempEnterprises)
            tempEnterprises.clear()
        print("Toutes les entreprises sont créées")
        timeDict["entreprise"] = time.time() - startEnterprise
    
    # Etablissements
    with open(f"{MEDIA_ROOT}{os.sep}establishment.csv", newline='', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        tempEstablishments = []
        startEstablishment = time.time()
        for row in reader:
            newEstablishment = dict(
                establishmentNumber=int(row["EstablishmentNumber"].replace(".", "")),
                enterpriseNumber= int(row["EnterpriseNumber"].replace(".", ""))
            )
            tempEstablishments.append(newEstablishment)
            count += 1
            if count % BULK_SIZE == 0:
                addEstablishment(tempEstablishments)
                tempEstablishments.clear()
        if len(tempEstablishments) > 0:
            addEstablishment(tempEstablishments)
            tempEstablishments.clear()
            print("Tous les établissements sont créés")
        timeDict["etablissement"] = time.time() - startEstablishment
    
    # Adresses
    with open(f"{MEDIA_ROOT}{os.sep}address.csv", newline='', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        startAddress = time.time()
        tempEnterprises = []
        tempEstablishments = []
        accepted_establishment_address_codes = ["BAET", "OBAD"]
        for row in reader:
            objectToUpdate = dict(
                    entityNumber = int(row["EntityNumber"].replace(".", "")),
                    country = row["CountryFR"] or "Belgique",
                    city= row["MunicipalityFR"],
                    zip = row["Zipcode"],
                    street = row["StreetFR"],
                    number = row["HouseNumber"],
                    box = row["Box"],
                    extraAddressInfo = row["ExtraAddressInfo"]
                )
            if len(row["EntityNumber"]) == 12:
                tempEnterprises.append(objectToUpdate)
            elif len(row["EntityNumber"]) == 13 and row["TypeOfAddress"] in accepted_establishment_address_codes:
                tempEstablishments.append(objectToUpdate)
            else:
                continue

            if len(tempEnterprises) == BULK_SIZE:
                addAddresses(tempEnterprises, "enterprise")
                tempEnterprises.clear()
                count += BULK_SIZE
            elif len(tempEstablishments) == BULK_SIZE:
                addAddresses(tempEstablishments, "establishment")
                tempEstablishments.clear()
                count += BULK_SIZE

        if len(tempEnterprises) > 0:
            addAddresses(tempEnterprises, "enterprise")
            tempEnterprises.clear()
        if len(tempEstablishments) > 0:
            addAddresses(tempEstablishments, "establishment")
            tempEstablishments.clear()
        print("Toutes les adresses ont été mises à jour")
        timeDict["addresse"] = time.time() - startAddress
    
    # Denominations
    with open(f"{MEDIA_ROOT}{os.sep}denomination.csv", newline='', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        startDenom = time.time()
        accepted_denoms = ["001", "003"] # Dénomination ou Dénomination commerciale
        tempEnterprisesDenom, tempEnterprisesComme, tempEstablishmentsDenom, tempEstablishmentsComme = [],[],[],[]
        for row in reader:
            if row["TypeOfDenomination"] not in accepted_denoms:
                continue

            objectToUpdate = dict(entityNumber = int(row["EntityNumber"].replace(".", "")))

            if row["TypeOfDenomination"] == "001":
                objectToUpdate["denomination"] = row["Denomination"]
            elif row["TypeOfDenomination"] == "003":
                objectToUpdate["commercialDenomination"] = row["Denomination"]

            if len(row["EntityNumber"]) == 12:
                if row["TypeOfDenomination"] == "001" and not any(e["entityNumber"] == int(row["EntityNumber"].replace(".", "")) for e in tempEnterprisesDenom):
                    tempEnterprisesDenom.append(objectToUpdate)
                elif row["TypeOfDenomination"] == "003" and not any(e["entityNumber"] == int(row["EntityNumber"].replace(".", "")) for e in tempEnterprisesComme):
                    tempEnterprisesComme.append(objectToUpdate)
                else:
                    continue
            elif len(row["EntityNumber"]) == 13:
                if row["TypeOfDenomination"] == "001" and not any(e["entityNumber"] == int(row["EntityNumber"].replace(".", "")) for e in tempEstablishmentsDenom):
                    tempEstablishmentsDenom.append(objectToUpdate)
                elif row["TypeOfDenomination"] == "003" and not any(e["entityNumber"] == int(row["EntityNumber"].replace(".", "")) for e in tempEstablishmentsComme):
                    tempEstablishmentsComme.append(objectToUpdate)
                else:
                    continue
        
            if len(tempEnterprisesDenom) == BULK_SIZE:
                addDenomination(tempEnterprisesDenom, "enterprise", "denomination")
                tempEnterprisesDenom.clear()
                count += BULK_SIZE
            elif len(tempEnterprisesComme) == BULK_SIZE:
                addDenomination(tempEnterprisesComme, "enterprise", "commercialDenomination")
                tempEnterprisesComme.clear()
                count += BULK_SIZE
            elif len(tempEstablishmentsDenom) == BULK_SIZE:
                addDenomination(tempEstablishmentsDenom, "establishment", "denomination")
                tempEstablishmentsDenom.clear()
                count += BULK_SIZE
            elif len(tempEstablishmentsComme) == BULK_SIZE:
                addDenomination(tempEstablishmentsComme, "establishment", "commercialDenomination")
                tempEstablishmentsComme.clear()
                count += BULK_SIZE

        if len(tempEnterprisesDenom) > 0:
            addDenomination(tempEnterprisesDenom, "enterprise", "denomination")
            tempEnterprisesDenom.clear()
            count += BULK_SIZE
        if len(tempEnterprisesComme) > 0:
            addDenomination(tempEnterprisesComme, "enterprise", "commercialDenomination")
            tempEnterprisesComme.clear()
            count += BULK_SIZE
        if len(tempEstablishmentsDenom) > 0:
            addDenomination(tempEstablishmentsDenom, "establishment", "denomination")
            tempEstablishmentsDenom.clear()
            count += BULK_SIZE
        if len(tempEstablishmentsComme) > 0:
            addDenomination(tempEstablishmentsComme, "establishment", "commercialDenomination")
            tempEstablishmentsComme.clear()
            count += BULK_SIZE
        print("Toutes les dénominations ont été mises à jour")
        timeDict["denomination"] = time.time() - startDenom
    
    print("Fin étape - Mise en DB")
    
    files = [f for f in os.listdir(f"{MEDIA_ROOT}") if f.endswith(".csv")]
    for file in files:
        os.remove(f"{MEDIA_ROOT}{os.sep}{file}")
    print("Etape effectuée - Suppression des fichiers csv")
    end = time.time()
    timeDict["total"] = end - start
    print(timeDict)

# Méthode pour ajouter/modifier les entreprises en DB (SQL) 
def addEntreprise(objs):
    arguments = ", ".join(["(%s, %s)" for _ in range(len(objs))])
    values = [v for d in objs for k, v in d.items()]
    with connection.cursor() as cursor:
        cursor.execute(
            f"""INSERT INTO companies_enterprise ("enterpriseNumber", active) 
            VALUES {arguments}
            ON CONFLICT ("enterpriseNumber") DO UPDATE 
                SET active = excluded.active;""", values)

# Méthode pour ajouter/modifier les établissements en DB (SQL)         
def addEstablishment(objs):
    arguments = ", ".join(["(%s, %s)" for _ in range(len(objs))])
    values = [v for d in objs for k, v in d.items()]
    with connection.cursor() as cursor:
        cursor.execute(
            f"""INSERT INTO companies_establishment ("establishmentNumber", "enterpriseNumber") 
            VALUES {arguments}
            ON CONFLICT ("establishmentNumber") DO UPDATE 
                SET "enterpriseNumber" = excluded."enterpriseNumber";""", values)

# Méthode pour ajouter/modifier les adresses en DB (SQL) 
def addAddresses(objs:list,type:str):
    arguments = ", ".join(["(%s, %s, %s, %s, %s, %s, %s, %s)" for _ in range(len(objs))])
    values = [v for d in objs for k, v in d.items()]
    with connection.cursor() as cursor:
        cursor.execute(
            f"""INSERT INTO companies_{type} ("{type}Number", country, city, zip, street, number, box, "extraAddressInfo") 
            VALUES {arguments}
            ON CONFLICT ("{type}Number") DO UPDATE 
                SET country = excluded.country, 
                    city = excluded.city,
                    zip = excluded.zip,
                    street = excluded.street,
                    number = excluded.number,
                    box = excluded.box,
                    "extraAddressInfo" = excluded."extraAddressInfo";""", values)

# Méthode pour ajouter/modifier les dénominations en DB (SQL) 
def addDenomination(objs:list, type:str, field:str):
    arguments = ", ".join(["(%s, %s)" for _ in range(len(objs))])
    values = [v for d in objs for k, v in d.items()]
    correctedField = field if field == 'denomination' else '"'+field+'"'
    with connection.cursor() as cursor:
        cursor.execute(
            f"""INSERT INTO companies_{type} ("{type}Number", {correctedField}) 
            VALUES {arguments}
            ON CONFLICT ("{type}Number") DO UPDATE 
                SET {correctedField} = excluded.{correctedField};""", values)

# Méthode de recherche des entreprises via la recherche par dénomination / numéro (+ complète l'adresse si vide avec celle du première établissement)
@api_view(['GET'])
@permission_classes([IsAuthenticated])    
def searchEnterprises(request):
    query = request.GET.get("q")
    enterprises= []
    if len(query) >= 3:
        if (len(query) > 2 and query[:2] == "BE" and query[2].isnumeric()) or query[:3].isnumeric():
            if query[:2].isalpha():
                query = query[2:]
            if query[0] == "0":
                query = query[1:]
            query = query.replace(" ", "").replace(".", "")
            enterprises = Enterprise.objects.filter(enterpriseNumber__icontains=query).values().order_by("denomination")[:100]

        else:
            enterprises = Enterprise.objects.filter(denomination__icontains=query).values().order_by("denomination")[:100]
    for e in enterprises:
        if e["street"] == None:
            esta = Establishment.objects.filter(enterprise_id=e["enterpriseNumber"]).first()
            if esta != None:
                e["street"] = esta.street
                e["city"] = esta.city
                e["zip"] = esta.zip
                e["street"] = esta.street
                e["number"] = esta.number
                e["box"] = esta.box
                e["extraAddressInfo"] = esta.extraAddressInfo
                e["country"] = esta.country
        else:
            continue   
    serializer = EnterpriseSerializer(enterprises, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Méthode pour retourner une entreprise et est complété avec l'adresse de son premier établissement si l'adresse est vide
@api_view(['GET'])
@permission_classes([IsAuthenticated])    
def getEnterprise(request, pk):
    enterprise = Enterprise.objects.get(pk=pk)
    if enterprise.street == None:
        esta = Establishment.objects.filter(enterprise_id=enterprise.enterpriseNumber).first()
        if esta != None:
            enterprise.street = esta.street
            enterprise.city = esta.city
            enterprise.zip = esta.zip
            enterprise.street = esta.street
            enterprise.number = esta.number
            enterprise.box = esta.box
            enterprise.extraAddressInfo = esta.extraAddressInfo
            enterprise.country = esta.country
    serializer = EnterpriseSerializer(enterprise)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Méthode retournant les établissements d'une entreprise via son numéro d'entreprise
@api_view(['GET'])
@permission_classes([IsAuthenticated])    
def getEnterpriseEstablishments(request, pk):
    establishments = Establishment.objects.filter(enterprise_id = pk)
    serializer = EstablishmentSerializer(establishments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
