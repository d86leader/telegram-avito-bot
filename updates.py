from db import DbAccess
from parserr.parserr import get_ads_list, get_new_ads
from main import bot
import time

from typing import Tuple


def send_updates(db: DbAccess) -> Tuple[int, int]:
    sce = db.get_search_collection_entries()
    total = 0
    total_new = 0

    for i in sce:
        tracking_urls = []
        for url in i['tracking_urls']:
            old_ads = url['ads']
            actual_ads = get_ads_list(url['url'])
            total += len(actual_ads)
            new_ads = get_new_ads(actual_ads, old_ads)

            for new_ad in new_ads:
                total_new += 1
                title = new_ad.title.rstrip() + "\n"
                price = new_ad.price.rstrip() + "\n" if new_ad.price else ""
                msg = title + price + new_ad.url

                bot.send_message(i['uid'], msg)

            url['ads'] = [x.to_dict() for x in actual_ads]
            tracking_urls.append(url)

            import random
            time.sleep(random.randint(1, 15) / 10)

        db.set_actual_ads(i['uid'], tracking_urls)

    return (total_new, total)


if __name__ == '__main__':
    db = DbAccess()
    import schedule # type: ignore

    send_updates(db)
    schedule.every(2).minutes.do(lambda: send_updates(db))

    while True:
        schedule.run_pending()
        time.sleep(1)
