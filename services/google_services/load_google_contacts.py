# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from json import dumps, loads
from bson import json_util
from models import *
# các model User, GoogleAccount, OutlookAccount, Contact, SyncContacts
from zato.server.service import Service


class LoadGoogleContacts(Service):
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

    if not googleAccount.activated :
      response.payload = {
        'success': False,
        'message': 'Google account not linked'
      }
      response.status_code = 400
      return

    res_load_contacts = self.loadContacts(googleAccount.access_token)

    if res_load_contacts['status_code'] == 200 :
      if res_load_contacts['data'] :
        listContacts =  res_load_contacts['data']['connections']
        googleAccount.contacts = self.saveContacts(listContacts)
        googleAccount.email = self.getEmailAccount(googleAccount.access_token)
      else :
        googleAccount.contacts = []
      user.save()
      response.payload = {
        'success': True,
        'message': 'Load and save Google contacts successfully'
      }
      response.status_code = 200
      return

    elif res_load_contacts['status_code'] == 401 :
      result = self.refreshGoogleAccessToken(googleAccount.refresh_token)
      if result['status'] :
        googleAccount.access_token = result['access_token']       
        res_load_contacts = self.loadContacts(googleAccount.access_token)
        if res_load_contacts['data'] :
          listContacts =  res_load_contacts['data']['connections']
          googleAccount.contacts = self.saveContacts(listContacts)
          googleAccount.email = self.getEmailAccount(googleAccount.access_token)
        else :
          googleAccount.contacts = []
        user.save()
        response.payload = {
          'success': True,
          'message': 'Load and save Google contacts successfully'
        }
        response.status_code = 200
        return

      else :
        googleAccount.activated = False
        googleAccount.email = None
        googleAccount.access_token = None
        googleAccount.refresh_token = None
        user.save()
        response.payload = {
          'success': False,
          'message': 'Google account not linked'
        }
        response.status_code = 400
        return
    
    response.payload = {
      'success': False,
      'message': 'An error has occurred'
    }
    response.status_code = 400


  ############################################

  def loadContacts(self, accessToken):
    load_contacts_conn = self.outgoing.plain_http['Load Google Contacts'].conn

    params = {
      'personFields': 'names,phoneNumbers'
    }
    payload = {
      # Không có payload trong body
    }

    googleToken = 'Bearer ' + accessToken
    headers = {
      'Content-Type': 'application/json',
      'Authorization': googleToken
    }
    # Gửi get request lấy danh bạ google
    res_load_contacts = load_contacts_conn.get(self.cid, params, headers=headers)

    return {
      'status_code': res_load_contacts.status_code,
      'data': res_load_contacts.json()
    }

  def getEmailAccount(self, accessToken):
    get_email_conn = self.outgoing.plain_http['Load Google Account'].conn

    params = {
      # Không có params
    }
    payload = {
      # Không có payload trong body
    }

    googleToken = 'Bearer ' + accessToken
    headers = {
      'Content-Type': 'application/json',
      'Authorization': googleToken
    }
    # Gửi get request lấy danh bạ outlook
    res_get_email = get_email_conn.get(self.cid, params, headers=headers)

    return res_get_email.json()['email']


  def refreshGoogleAccessToken(self, refreshToken):
    # Khai báo kết nối tới api trao đổi token của google
    exchange_token_conn = self.outgoing.plain_http['Exchange Google Token'].conn

    params = {
      # Không có params
    }
    payload = {
      'client_id': '301608552892-g7inqpodo0dkvlvkmnaqrmpgf8oi695d.apps.googleusercontent.com',
      'client_secret': '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',
      'refresh_token': refreshToken,
      'grant_type': 'refresh_token'
    }
    headers = {
      'Content-Type': 'application/json'
    }

    res_exchange_token = exchange_token_conn.post(self.cid, payload, params, headers=headers)

    # self.logger.info(res_exchange_token.data)
    # self.logger.info(res_exchange_token.status_code)
    
    self.logger.info('Goi den refresh roi ...............!')

    if res_exchange_token.status_code == 200 :
      return {
        'status': True,
        'access_token': res_exchange_token.data['access_token']
      }
    else :
      return {
        'status': False
      }
    
  
  def saveContacts(self, dataContacts):
    contacts = []
    for item in dataContacts :
      resourceName = item['resourceName']
      etag = item['etag']
      phoneName = item['names'][0]['displayName']
      phoneNumbers = []
      for phoneNumber in item['phoneNumbers'] :
        phoneNumbers.append(phoneNumber['value'])
      contact = GoogleContact(resource_name=resourceName, etag=etag, phone_name=phoneName, phone_numbers=phoneNumbers)
      contacts.append(contact)
    
    return contacts
