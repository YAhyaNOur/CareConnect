from django.db import models



class Medecin(models.Model):
    firstname=models.CharField(max_length=20)
    lastname=models.CharField(max_length=20)
    email=models.EmailField(max_length=100,unique=True)
    telephonenumber=models.CharField(max_length=80)
    specialite=models.CharField(max_length=100)
    localisation_cabinet=models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    password=models.CharField(max_length= 128)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
   
    def __str__(self):
        return f"{self.firstname} {self.lastname}"
    

class patient_insc(models.Model) :
    Name = models.CharField(max_length = 50 , default = "" )
    my_email =  models.EmailField(max_length = 100  , default = "" )
    my_password = models.CharField(max_length=128)
    passw = models.CharField(max_length=128)
    Sexe =  models.CharField(max_length = 1 , default = "" )
    NumTel =  models.IntegerField(blank = False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    verification_code = models.CharField(max_length=6, blank=True, null=True)



class emp_auth(models.Model):
    email = models.EmailField(max_length=100, default="")
    password = models.CharField(max_length=30)


class psy_insc(models.Model) :
    Name = models.CharField(max_length = 50 , default = "" )
    email =  models.EmailField(max_length = 100  , default = "" )
    password = models.CharField(max_length=128)
    passw = models.CharField(max_length=128)
    fichiers = models.FileField(upload_to='fichiers')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    localisation_cabinet = models.CharField(max_length=150, blank=True, default="")
    verification_code = models.CharField(max_length=6, blank=True, null=True)

class RDV(models.Model):
    date = models.DateField()
    email =  models.EmailField(max_length = 100  , default = "" )
    DocName = models.CharField()

class ConfPsy (models.Model) :
    Name = models.CharField()
    photo = models.ImageField()
    desc = models.CharField()                                        




