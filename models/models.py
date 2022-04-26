from mongoengine import *

connect(host="mongodb+srv://user_01:user_01@cluster0.t4ua1.mongodb.net/app_tism_zato_mudule?retryWrites=true&w=majority")

class Contact(EmbeddedDocument):
  phone_name = StringField(max_length=100)
  phone_numbers = ListField(StringField())

class GoogleContact(EmbeddedDocument):
  resource_name = StringField(max_length=100)
  etag = StringField(max_length=100)
  phone_name = StringField(max_length=100)
  phone_numbers = ListField(StringField())

class OutlookContact(EmbeddedDocument):
  id = StringField(max_length=1000)
  phone_name = StringField(max_length=100)
  phone_numbers = ListField(StringField())

class GoogleAccount(EmbeddedDocument):
  activated = BooleanField(required=True, default=False)
  email = StringField()
  access_token = StringField()
  refresh_token = StringField()
  contacts = ListField(EmbeddedDocumentField(GoogleContact))

class OutlookAccount(EmbeddedDocument):
  activated = BooleanField(required=True, default=False)
  email = StringField()
  access_token = StringField()
  refresh_token = StringField()
  contacts = ListField(EmbeddedDocumentField(OutlookContact))

class SyncContacts(EmbeddedDocument):
  contacts = ListField(EmbeddedDocumentField(Contact))
  sync_at = DateTimeField()

class User(Document):
  user_id = StringField(required=True, unique=True)
  google = EmbeddedDocumentField(GoogleAccount)
  outlook = EmbeddedDocumentField(OutlookAccount)
  sync_contacts = EmbeddedDocumentField(SyncContacts)
  
  meta = {
    'collection': 'user_contacts'
  }