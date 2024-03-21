from django.db import models
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError
from uuid_extensions import uuid7
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class UserRole(models.TextChoices):
        ADMIN = "ADMIN", _("Admin")
        SALES = "SALES", _("Commercial")
    role = models.CharField(max_length=5,choices=UserRole.choices, default=UserRole.ADMIN)

class CustomerBilling(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7(), editable=False)
    name = models.CharField(max_length = 200)
    company_number = models.CharField(max_length = 200,null=True, blank=True)
    address1 = models.CharField(max_length = 200)
    address2 = models.CharField(max_length = 200,null=True, blank=True)
    zip = models.CharField(max_length = 200)
    city = models.CharField(max_length = 200)
    country = models.CharField(max_length = 200)
    phone = models.CharField(max_length = 200,null=True, blank=True)
    mail = models.CharField(max_length = 200,null=True, blank=True)

    def __str__(self) -> str:
        return self.name

class CustomerDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7(), editable=False)
    name = models.CharField(max_length = 200)
    address1 = models.CharField(max_length = 200)
    address2 = models.CharField(max_length = 200,null=True, blank=True)
    zip = models.CharField(max_length = 200)
    city = models.CharField(max_length = 200)
    country = models.CharField(max_length = 200)
    phone = models.CharField(max_length = 200,null=True, blank=True)
    mail = models.CharField(max_length = 200,null=True, blank=True)

    class Meta:
        verbose_name_plural = "CustomerDeliveries"

    def __str__(self) -> str:
        return self.name

class CustomerContact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7(), editable=False)
    first_name = models.CharField(max_length = 200,null=True, blank=True)
    last_name = models.CharField(max_length = 200,null=True, blank=True)
    phone = models.CharField(max_length = 200,null=True, blank=True)
    mail = models.CharField(max_length = 200,null=True, blank=True)

    def clean(self) -> None:
        if self.first_name == '' and self.last_name == '':
            raise ValidationError("Au moins un des 2 champs doit être rempli (Prénom et Nom)")
        if self.phone == '' and self.mail == '':
            raise ValidationError("Au moins un des 2 champs doit être rempli (Numéro de téléphone et Email)")
        return self
    
    def infos(self) -> str:
        if self.phone is None:
            return self.mail
        elif self.mail is None:
            return self.phone
        return f"{self.mail} {self.phone}"

    def __str__(self) -> str:
        if self.first_name is None:
            return self.last_name
        elif self.last_name is None:
            return self.first_name
        return f"{self.first_name} {self.last_name}"

class CustomerOrder(models.Model):
    class CustomerStatus(models.TextChoices):
        CREATED = "created", _("En cours de création")
        BOARDING = "boarding", _("Boarding")
        PROCESSING = "processing", _("En traitement")
        WAITING_CUSTOMER = "waiting_customer", _("En attente avec le client")
        WAITING_THIRD_PARTY = "waiting_third_party", _("En attente avec tiers partie")
        COMPLETE = "complete", _("Complet")
        CANCELED = "canceled", _("Annulé")
        ABANDONED = "abandoned", _("Abandonné")
    id = models.UUIDField(primary_key=True, default=uuid7(), editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length = 19,
        choices=CustomerStatus.choices,
        default = CustomerStatus.CREATED
    )
    customer_comment = models.TextField(null=True, blank=True)
    billing = models.ForeignKey(CustomerBilling, on_delete=models.CASCADE, blank = True, null=True)
    delivery = models.ForeignKey(CustomerDelivery, on_delete=models.CASCADE, blank = True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank = True, null=True, related_name='orders')
    contacts = models.ManyToManyField(CustomerContact)

    def total(self) -> float:
        order_lines = list(OrderLine.objects.filter(order = self))
        return sum(line.quantity * line.price for line in order_lines)
    
    def __str__(self) -> str:
        if self.delivery is None:
            return f"Bon de commande - {self.user.username} - {self.created_at.strftime('%d-%m-%Y %H:%M:%S')}"
        return f"Bon de commande - {self.user.username} - {self.delivery.name} - {self.created_at.strftime('%d-%m-%Y %H:%M:%S')}"

class CustomerFinancial(models.Model):
    class FinancingType(models.TextChoices):
        CASH = 'Cash', 'Cash'
        BANK = 'Bank', 'Bank'
        OTHER = 'Other', 'Other'  
    class BankDuration(models.IntegerChoices):
        NA = 0, 'Not applicable'
        TWO_YEAR = 2, 'Two Years'
        THREE_YEARS = 3, 'Three Years'
        FOUR_YEARS = 4, 'Four Years'
        FIVE_YEARS = 5, 'Five Years'
    id = models.UUIDField(primary_key=True, default=uuid7(), editable=False)
    type = models.CharField(
        max_length=50,
        choices=FinancingType.choices,
        default=FinancingType.CASH,
    )
    comment = models.CharField(max_length=200, null=True, blank=True)
    bankDuration =  models.IntegerField(
        choices=BankDuration.choices,
        default=BankDuration.NA,
        null=True,
    )
    def __str__(self):
        return f"CustomerFinancial {self.id}"

class Attachment(models.Model):
    class AttachmentType(models.TextChoices):
        PASSPORT = "passport", _("Passport")
        FINANCIAL = "financial", _("Finance")
        SIGNATURE = "signature", _("Signature")
        OTHER = "other", _("Autre")
    id = models.UUIDField(primary_key=True, default=uuid7(), editable=False)
    type = models.CharField(
        max_length = 9,
        choices=AttachmentType.choices,
        default = AttachmentType.OTHER
    )
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='attachment_files', blank = True, null=True)
    mime = models.CharField(max_length = 200)
    size = models.IntegerField(default=1)
    url = models.CharField(max_length = 200, default="")
    file = models.FileField(blank = True, null=True)
    filename = models.CharField(max_length=200, default="")

    def __str__(self) -> str:
        return self.url

class OrderLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7(), editable=False)
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='order_lines', blank = True, null=True)
    quantity = models.IntegerField(default = 1)
    description = models.CharField(max_length = 200)
    price = models.DecimalField(default = 0, max_digits=6, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.quantity} {self.description} à {self.price}€  => {self.total()}€"
    
    def total(self) -> float:
        return self.quantity * self.price
    
class OrderAction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7(), editable=False)
    description = models.CharField(max_length = 255)
    additionalContext = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='order_history', blank = True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank = True, null=True, related_name='order_actions')

class OrderComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7(), editable=False)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='order_comments', blank = True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank = True, null=True, related_name='user_comments')