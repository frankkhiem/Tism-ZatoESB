# -*- coding: utf-8 -*-
# zato: ide-deploy=True

from zato.server.service import Service


class AuthMiddleware(Service):
  """ Nhận request gồm accessToken xác thực và trả lại thông tin người dùng tương ứng
  """

  class SimpleIO:
    input_required = 'accessToken'

  def handle(self):
    # Khai báo đối tượng request và response của service
    request = self.request.input
    response = self.response

    accessToken = request['accessToken']
    
    # Khai báo kết nối tới api xác thực người dùng từ accessToken của firebase
    auth_conn = self.outgoing.plain_http['Auth User By AccessToken'].conn

    params = {
      # Không có params
    }
    payload = {
      # Không có payload trong body
    }

    headers = {
      'Content-Type': 'application/json',
      'Authorization' : 'Bearer ' + accessToken
    }

    # Gửi request tới firebase xác thực người dùng trả về res_auth
    res_auth = auth_conn.get(self.cid, params, headers=headers)

    # self.logger.info(res_auth.json().keys())

    if res_auth.status_code == 200:
      response.payload = {
        'auth': True,
        'userId': res_auth.json()['userId']
      }
      response.status_code = 200

    else:
      response.payload = {
        'auth': False,
        'message': 'Unauthorized'
      }
      response.status_code = res_auth.status_code

    return