from django.db import connection, models
from uuid_extensions import uuid7

class Enterprise(models.Model):
    enterpriseNumber = models.PositiveBigIntegerField(primary_key=True, editable=True)
    active = models.BooleanField(default=True, null=True)
    denomination = models.CharField(max_length = 320,null=True, blank=True)
    commercialDenomination = models.CharField(max_length = 320,null=True, blank=True)
    country = models.CharField(max_length = 100, default="Belgique",null=True, blank=True)
    zip = models.CharField(max_length = 20,null=True, blank=True)
    city = models.CharField(max_length = 200,null=True, blank=True)
    street = models.CharField(max_length = 200,null=True, blank=True)
    number = models.CharField(max_length = 22,null=True, blank=True)
    box = models.CharField(max_length = 20,null=True, blank=True)
    extraAddressInfo = models.CharField(max_length = 80,null=True, blank=True)

    def __str__(self):
        return str(self.enterpriseNumber)
    
    # Méthode de classe permettant de faire un TRUNCATE sur la table enterprise
    @classmethod
    def truncate(cls):
        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE TABLE {} CASCADE;'.format(cls._meta.db_table))

class Establishment(models.Model):
    establishmentNumber = models.PositiveBigIntegerField(primary_key=True, editable=True)
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, db_column='enterpriseNumber', null=True)
    denomination = models.CharField(max_length = 320,null=True, blank=True)
    commercialDenomination = models.CharField(max_length = 320,null=True, blank=True)
    country = models.CharField(max_length = 100, default="Belgique",null=True, blank=True)
    zip = models.CharField(max_length = 20,null=True, blank=True)
    city = models.CharField(max_length = 200,null=True, blank=True)
    street = models.CharField(max_length = 200,null=True, blank=True)
    number = models.CharField(max_length = 22,null=True, blank=True)
    box = models.CharField(max_length = 20,null=True, blank=True)
    extraAddressInfo = models.CharField(max_length = 80,null=True, blank=True)

    def __str__(self):
        return str(self.establishmentNumber)

class AlertAddress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7(), editable=False)
    establishmentNumber = models.ForeignKey(Establishment, on_delete=models.CASCADE, blank = True, null=True,db_column='establishmentNumber')
    enterpriseNumber = models.ForeignKey(Enterprise, on_delete=models.CASCADE, blank = True, null=True,db_column='enterpriseNumber')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.enterpriseNumber if self.enterpriseNumber != None else self.establishmentNumber} - {self.created_at.strftime('%d-%m-%Y %H:%M:%S')}"


