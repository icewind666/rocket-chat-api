from urllib.parse import urljoin
import requests


class RocketChatClient(object):
    """
    Rocketchat api client.

    """
    RC_SUCCESS = 'success'

    def __init__(self, url):
        """
        Creates RocketChat Rest API client.
        Does not perform login or any other request.
        :param url: Rocket.Chat server url.
        """
        self._session = requests.session()

        self._url = url

        if not (url.startswith('http://') or url.startswith('https://')):
            raise ValueError('Rocket.Chat server url must start with either http:// or https://')

        make_url = lambda endpoint: urljoin(self._url, endpoint)

        self._url_info = make_url('/api/info')

        # auth
        self._url_login = make_url('/api/login')
        self._url_logout = make_url('/api/logout')

        # public rooms
        self._url_public_rooms = make_url('/api/v1/channels.list.joined')

        # rooms
        base_rooms = make_url('/api/channels/{room_id}/')
        self._url_room_join = urljoin(base_rooms, 'join')
        self._url_room_leave = urljoin(base_rooms, 'leave')
        self._url_room_send = make_url('/api/v1/chat.postMessage')
        self._url_room_messages = make_url('/api/v1/channels.messages')

        # channels
        self._url_channel_create = make_url('/api/v1/channels.create')

        # user
        self._url_user_create = make_url('/api/v1/users.create')
        self._url_user_update = make_url('/api/v1/user.update')

    def get_info(self):
        return self._session.get(self._url_info).json()

    def login(self, user, password):
        r = self._session.post(self._url_login, data={'user': user, 'password': password})
        json = r.json()

        if json['status'] != self.RC_SUCCESS:
            raise NotLoggedIn(
                'Login request to {r.url} failed.\n'
                'Status code: {r.status_code}.\n'
                'Body: {r.text}'.format(r=r)
            )

        data = json['data']
        auth_headers = {
            'X-Auth-Token': data['authToken'],
            'X-User-Id': data['userId'],
            'Content-Type': 'application/json'
        }

        self._session.headers.update(auth_headers)

    def get_rooms(self):
        return self._get(self._url_public_rooms)

    def join_room(self, room_id):
        return self._post(self._url_room_join.format(room_id=room_id), check_json_status=False, return_json=False)

    def leave_room(self, room_id):
        return self._post(self._url_room_leave.format(room_id=room_id), check_json_status=False, return_json=False)

    def get_room_msgs(self, room_id):
        return self._get(self._url_room_messages.format(room_id=room_id))

    def send_room(self, room_id, msg):
        return self._post(self._url_room_send, json={'channel': room_id, 'text': msg})

    def create_channel(self, channel_name):
        return self._post(self._url_channel_create, json={'name': channel_name}, check_json_status=False)

    def create_user(self, name, email, password, username, customFields):
        """
        :param name: User's name
        :param email: User's email address
        :param password: User's password
        :param username: User's username/login
        :param customFields: dict of customFields, e.g. {'twitter': 'users twitter'}
        """
        data = dict(
            name=name,
            email=email,
            password=password,
            username=username,
            customFields=customFields
        )

        return self._post(self._url_user_create, json=data, check_json_status=False)

    def update_user(self, new_name, new_email):
        data = dict(
            userId='',  # via https://rocket.chat/docs/developer-guides/rest-api/
            data=dict(
                name=new_name,
                email=new_email
            )
        )
        return self._post(self._url_user_update, json=data)

    def _check_request_msg(self, method, r, expected_status_code, check_json_status):
        fail_msg = (
            "{type} to {r.url} failed - status code doesn't match the expected one.\n"
            "Got: {r.status_code}, expected: {expected_code}.\n"
            "Body: {r.text}".format(type=method, expected_code=expected_status_code, r=r)
        )

        if r.status_code != expected_status_code:
            raise RequestFailed(fail_msg)
        # r_json = r.json()
        # if check_json_status and r_json['status'] != self.RC_SUCCESS:
        #    raise RequestFailed(fail_msg)

    def _get(self, url, expected_code=200, check_json_status=True):
        r = self._session.get(url)

        self._check_request_msg('GET', r, expected_code, check_json_status)

        return r.json()

    def _post(self, url, json=None, expected_code=200, check_json_status=True, return_json=True):
        if not json:
            json = {}

        r = self._session.post(url, json=json)

        self._check_request_msg('POST', r, expected_code, check_json_status)

        if return_json:
            return r.json()


class RocketChatApiException(Exception):
    pass


class NotLoggedIn(RocketChatApiException):
    pass


class RequestFailed(RocketChatApiException):
    pass
