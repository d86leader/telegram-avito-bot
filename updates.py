import db
from parserr.parserr import get_ads_list, get_new_ads
from main import bot
import time


def send_updates():
    sce = db.get_search_collection_entries()

    for i in sce:
        tracking_urls = []
        for url in i['tracking_urls']:
            old_ads = url['ads']
            actual_ads = get_ads_list(url['url'])
            new_ads = get_new_ads(actual_ads, old_ads)

            for new_ad in new_ads:
                title = new_ad.title.rstrip() + "\n"
                price = new_ad.price.rstrip() + "\n" if new_ad.price else ""
                msg = title + price + new_ad.url

                # if new_ad['img']:
                #     from utils import get_img_file_by_url
                #
                #     img_file = get_img_file_by_url(new_ad['img'])
                #     if img_file:
                #         bot.send_photo(i['uid'], img_file)

                bot.send_message(i['uid'], msg)

            url['ads'] = actual_ads
            tracking_urls.append(url)

            import random
            time.sleep(random.randint(1, 15) / 10)

        db.set_actual_ads(i['uid'], tracking_urls)


if __name__ == '__main__':
    import schedule

    send_updates()
    schedule.every(2).minutes.do(send_updates)

    while True:
        schedule.run_pending()
        time.sleep(1)
