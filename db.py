from pymongo import MongoClient # type: ignore

class DbAccess:
    def __init__(self, address="mongodb", port=27017) -> None:
        client = MongoClient(address, port)
        db = client['mongoosito']
        self.search_collection = db['search_collection']
        self.search_url_and_name_interlayer = db['url_name_interlayer']

    def save_url_to_temp(self, uid, url):
        self._remove_url_from_temp(uid)
        return self.search_url_and_name_interlayer.insert_one({'uid': uid, 'url': url})


    def _remove_url_from_temp(self, uid):
        self.search_url_and_name_interlayer.delete_many({'uid': uid})


    def get_temp_url(self, uid):
        url = self.search_url_and_name_interlayer.find_one({'uid': uid})
        self._remove_url_from_temp(uid)
        return url['url']


    def save_url(self, uid, search_url, search_name):
        """
        :param uid: идентификатор чата
        :param search_url: название для поиска, например "Поиск машины для клиента"
        :param search_name: отслеживаемая ссылка, например: https://avito.ru/kazan/avto/vaz
        :return boolean: запись добавлена / не добавлена (ошибка бд)
        """
        from parserr import parserr
        self.search_collection.update_one({'uid': uid}, {'$push': {'tracking_urls': {
            'url': search_url,
            'name': search_name,
            'ads': [x.to_dict() for x in parserr.get_ads_list(search_url)]
        }}}, upsert=True)


    def is_link_already_tracking_by_user(self, uid, search_url):
        try:
            user_urls = self.search_collection.find_one({'uid': uid})
        except:
            raise Exception

        if user_urls is None or 'tracking_urls' not in user_urls:
            return False

        for _ in user_urls['tracking_urls']:
            if _['url'] == search_url:
                return True

        return False


    def get_search_collection_entries(self):
        return list(self.search_collection.find({}))


    def get_users_tracking_urls_list(self, uid):
        """
        :param uid: telegram user id
        :return: list of dicts [{'url': '', 'name': ''}]
        """
        user = self.search_collection.find_one({'uid': uid})

        if not user:
            return None

        tracking_urls = user['tracking_urls']

        _ = []
        for u in tracking_urls:
            _.append({
                'url': u['url'],
                'name': u['name']
            })
        return _


    def delete_url_from_tracking(self, uid, human_index):
        """
        :param uid:
        :param human_index: > 0, [12, 45, 17] human_index = 1 : 12, human_index = 3 : 17
        :return: boolean
        """
        user = self.search_collection.find_one({'uid': uid})

        if not user:
            return None

        tracking_urls = user['tracking_urls']
        try:
            del tracking_urls[human_index - 1]
            self.search_collection.update_one({'uid': uid}, {'$set': {
                'tracking_urls': tracking_urls
            }})
            return True
        except:
            return False


    def set_actual_ads(self, uid, tracking_urls):
        self.search_collection.update_one({'uid': uid}, {'$set': {
            'tracking_urls': tracking_urls
        }})
