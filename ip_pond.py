import requests
from scrapy.selector import Selector
import pymysql

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
}

# 这是自己的数据库
conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456', db='jobs', charset='utf8')
cursor = conn.cursor()


def update_ip_pond():
    # for i in range(3600):
    #     resp = requests.get('https://www.xicidaili.com/nn/{0}'.format(i), headers=headers)

    resp = requests.get('https://www.xicidaili.com/nn/1', headers=headers)
    selector = Selector(text=resp.text)
    all_items = selector.xpath('//*[@id="ip_list"]//tr')
    ip_list = []
    for item in all_items[1:]:
        # 这里使用xpath从网页提取
        speed_str = item.xpath('td[7]/div/@title').get()
        if speed_str:
            speed = float(speed_str.split('秒')[0])
        ip = item.xpath('td[2]/text()').get()
        port = item.xpath('td[3]/text()').get()
        proxy_type = item.xpath('td[6]/text()').get().lower()

        ip_list.append((ip, port, proxy_type, speed))
        for ip_info in ip_list:
            cursor.execute(
                "insert ip_pond(ip,port,proxy_type,speed) values ('{0}','{1}','{2}','{3}') ON DUPLICATE KEY UPDATE ip=VALUES(ip),port=VALUES(port),proxy_type=VALUES(proxy_type),speed=VALUES(speed)"
                    .format(ip_info[0], ip_info[1], ip_info[2], ip_info[3])
            )
        conn.commit()


class GetIp(object):

    # 删除不可用的Ip
    def delete_ip(self, ip):
        delete_sql = """
        DELETE FROM ip_pond WHERE ip='{0}'
        """.format(ip)
        cursor.execute(delete_sql)
        conn.commit()
        return True

    # 验证ip是否可用
    def judge_ip(self, ip, port, proxy_type):
        http_url = 'https://www.baidu.com'
        proxy_url = '{0}://{1}:{2}'.format(proxy_type, ip, port)
        try:
            if proxy_type == 'http':
                proxy_dict = {
                    'http': proxy_url
                }
            else:
                proxy_dict = {
                    'https': proxy_url
                }
            requests.get(http_url, proxies=proxy_dict)
            return True
        except Exception as e:
            print('invalid ip and port')
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >= 200 and code < 300:
                print('effective ip')
                return True
            else:
                print('invalid ip and port')
                self.delete_ip(ip)
                return False

    # 从数据库中随机选择
    def get_random_ip(self):
        random_sql = """
        SELECT ip,port,proxy_type,speed FROM ip_pond ORDER BY RAND() LIMIT 1
        """
        cursor.execute(random_sql)
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]
            proxy_type = ip_info[2]
            judge_re = self.judge_ip(ip, port, proxy_type)
            if judge_re:
                return '{0}://{1}:{2}'.format(proxy_type, ip, port)
            else:
                return self.get_random_ip()

    # 从数据库中选速度最快的
    def get_optimum_ip(self):
        optimum_sql = """
        SELECT ip,port,proxy_type,speed FROM ip_pond ORDER BY speed LIMIT 1
        """
        cursor.execute(optimum_sql)
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]
            proxy_type = ip_info[2]
            judge_re = self.judge_ip(ip, port, proxy_type)
            if judge_re:
                return '{0}://{1}:{2}'.format(proxy_type, ip, port)
            else:
                return self.get_optimum_ip()


if __name__ == '__main__':
    # 运行以下代码之前，需要先运行update_ip_pond()，将数据填入数据库

    url = 'https://www.baidu.com'
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"
    }
    getip = GetIp()
    ip = getip.get_random_ip()
    print(ip)
    proxy_type = ip.split(':')[0]
    proxies = {
        proxy_type: ip
    }
    res = requests.get(url=url, headers=headers, proxies=proxies)
    print(res)