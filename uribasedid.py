


class URIBasedIDBuilder(object) :
    @staticmethod
    def build(uuid, host, port, path):
        id = 'http://' + uuid + "@" + host + ":" + port + path;
        return  id


    @staticmethod
    def url( host, port, path):
        id = 'http://' + host + ":" + port + path;
        return  id
