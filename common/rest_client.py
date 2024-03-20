import json
import logging

import requests

logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.ERROR)


class RestClient(object):

    def __init__(self, cookies=None, log_level=logging.INFO):
        self.cookies = cookies
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8"
        }

        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(log_level)

    def set_authorization(self, authorization=None):
        if authorization is not None:
            self.headers['authorization'] = authorization

    def processed_response(self, res, json_response=True):
        if json_response:
            try:
                return res.json()
            except:
                self.log.exception('Cannot get json from response: %s, status code: %s', res.text, res.status_code)
                return None
        else:
            return res

    def update_headers(self, headers):
        request_headers = dict(self.headers)
        if headers is not None:
            request_headers.update(headers)
        return request_headers

    def get(self, url, json_response=True, headers=None):
        self.log.debug("GET %s", url)
        headers = self.update_headers(headers)
        res = requests.get(url, cookies=self.cookies, headers=headers)
        return self.processed_response(res, json_response)

    def post(self, url, payload, json_response=True, headers=None):
        json_payload = json.dumps(payload, indent=2)
        self.log.debug("POST %s\n%s\n%s", url, headers, json_payload)
        headers = self.update_headers(headers)
        res = requests.post(url, cookies=self.cookies, data=json_payload, headers=headers)
        return self.processed_response(res, json_response)

    def put(self, url, payload, json_response=True, headers=None):
        json_payload = json.dumps(payload, indent=2)
        self.log.debug("PUT %s\n%s", url, json_payload)
        headers = self.update_headers(headers)
        res = requests.put(url, cookies=self.cookies, data=json_payload, headers=headers)
        return self.processed_response(res, json_response)

    def delete(self, url, json_response=True, headers=None):
        self.log.debug("DELETE %s", url)
        headers = self.update_headers(headers)
        res = requests.delete(url, cookies=self.cookies, headers=headers)
        return self.processed_response(res, json_response)
