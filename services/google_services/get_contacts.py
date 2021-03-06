# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class GetGoogleContacts(Service):
  """ Nhận request gồm accessToken lấy user tương ứng, 
      lấy thông tin danh bạ google qua api từ tài khoản liên kết của user
  """

  class SimpleIO:
    input_required = 'accessToken'

  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response
    # Set headers tránh lỗi CORS
    response.headers = {
      'Access-Control-Allow-Origin' : '*',
    }

    ##############################################################################################
    # Mọi service cần xác thực người dùng và lấy thông tin của người đều cần các dòng trong vùng #
    accessToken = request['accessToken']

    input = {
      'accessToken': accessToken
    }

    # Gọi auth middleware xác thực người dùng thông qua accessToken
    res_auth = self.invoke('auth-middleware.auth-middleware', input)

    if not res_auth['auth']:
      response.payload = {
        'success': False,
        'message': 'Unauthorized'
      }
      response.status_code = 401
      return
    
    else:
      # userId nhận được dùng để query dữ liệu tương ứng với người dùng request đến
      userId = res_auth['userId']
    ##############################################################################################
    
    user = User.objects(user_id = userId)[0]
    googleAccount = user.google # object của model GoogleAccount

    googleContacts = [
      {
        'phoneName': contact.phone_name,
        'phoneNumbers': [
          phoneNumber
          for phoneNumber in contact.phone_numbers
        ]
      }
      for contact in googleAccount.contacts
    ]

    googleContacts.sort(key = lambda x: x['phoneName'].lower())
    
    response.payload = {
      'linked': googleAccount.activated,
      'account': googleAccount.email,
      'contacts': googleContacts
    }

    response.status_code = 200