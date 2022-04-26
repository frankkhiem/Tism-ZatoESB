# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from models import *
# các model User, GoogleAccount, Contact, ...
from zato.server.service import Service


class CreateUserContacts(Service):
  """ Nhận request tạo một kho danh bạ cho người dùng mới
  """

  class SimpleIO:
    input_required = 'userId'

  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response
    # Set headers tránh lỗi CORS
    response.headers = {
      'Access-Control-Allow-Origin' : '*',
    }

    userId = request['userId']

    response.payload = self.createUser(userId)
    response.status_code = 200

    return
  
  def createUser(self, userId):
    newUserContacts = User()
    newUserContacts.user_id = userId
    newUserContacts.google = GoogleAccount()
    newUserContacts.outlook = OutlookAccount()
    newUserContacts.sync_contacts = SyncContacts()

    newUserContacts.save()
    return {
      'userContactsId': str(newUserContacts.id),
      'success': True,
      'message': 'Create user contacts successfully!'
    }
