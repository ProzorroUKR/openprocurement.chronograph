# -*- coding: utf-8 -*-
import unittest
from datetime import datetime, timedelta
from copy import deepcopy
from iso8601 import parse_date
from time import sleep
from logging import getLogger

from openprocurement.chronograph import TZ
from openprocurement.chronograph.scheduler import planning_auction, free_slot
from openprocurement.chronograph.tests.base import BaseWebTest, BaseTenderWebTest, test_tender_data

from openprocurement.tender.belowthreshold.tests.base import test_bids
from openprocurement.tender.belowthreshold.tests.base import test_lots


LOGGER = getLogger(__name__)
test_tender_data_quick = deepcopy(test_tender_data)
test_tender_data_quick.update({
    "enquiryPeriod": {
        'startDate': datetime.now(TZ).isoformat(),
        "endDate": datetime.now(TZ).isoformat()
    },
    'tenderPeriod': {
        'startDate': datetime.now(TZ).isoformat(),
        "endDate": datetime.now(TZ).isoformat()
    }
})
test_tender_data_test_quick = deepcopy(test_tender_data_quick)
test_tender_data_test_quick['mode'] = 'test'


class SimpleTest(BaseWebTest):

    def test_list_jobs(self):
        response = self.app.get('/')
        self.assertEqual(response.status, '200 OK')
        self.assertIn('jobs', response.json)
        self.assertEqual(len(response.json['jobs']), 1)

    def test_resync_all(self):
        response = self.app.get('/resync_all')
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)

    def test_resync_back(self):
        response = self.app.get('/resync_back')
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)

    def test_resync_one(self):
        response = self.app.get('/resync/all')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)

    def test_recheck_one(self):
        response = self.app.get('/recheck/all')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)

    def test_calendar(self):
        response = self.app.get('/calendar')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, [])

    def test_calendar_entry(self):
        response = self.app.get('/calendar/2015-04-23')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, False)
        response = self.app.post('/calendar/2015-04-23')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, True)
        response = self.app.delete('/calendar/2015-04-23')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, False)
        response = self.app.get('/calendar/2015-04-23')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, False)

    def test_streams(self):
        response = self.app.get('/streams')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, 10)
        response = self.app.post('/streams', {'streams': 20})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, True)
        response = self.app.get('/streams')
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, 20)
        response = self.app.post('/streams', {'streams': -20})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, False)
        response = self.app.post('/streams', {'streams': 10})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, True)


class TendersTest(BaseTenderWebTest):

    def test_list_jobs(self):
        response = self.app.get('/')
        self.assertEqual(response.status, '200 OK')
        self.assertIn('jobs', response.json)
        self.assertEqual(len(response.json['jobs']), 1)
        self.assertIn('resync_all', response.json['jobs'])
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        response = self.app.get('/')
        self.assertEqual(response.status, '200 OK')
        self.assertIn('jobs', response.json)
        self.assertEqual(len(response.json['jobs']), 2)
        self.assertIn("recheck_{}".format(self.tender_id), response.json['jobs'])

    def test_resync_all(self):
        response = self.app.get('/resync_all')
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        sleep(0.1)
        response = self.app.get('/')
        self.assertEqual(response.status, '200 OK')
        self.assertIn('jobs', response.json)
        self.assertEqual(len(response.json['jobs']), 2)
        self.assertIn("recheck_{}".format(self.tender_id), response.json['jobs'])


class TenderTest(BaseTenderWebTest):
    scheduler = False

    def test_wait_for_enquiryPeriod(self):
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.enquiries')

    def test_switch_to_tendering_enquiryPeriod(self):
        response = self.api.patch_json(self.app.app.registry.api_url + 'tenders/' + self.tender_id, {
            'data': {
                "enquiryPeriod": {
                    "endDate": datetime.now(TZ).isoformat()
                },
                'tenderPeriod': {
                    'startDate': datetime.now(TZ).isoformat()
                }
            }
        })
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.tendering')

    def test_switch_to_tendering_tenderPeriod(self):
        response = self.api.patch_json(self.app.app.registry.api_url + 'tenders/' + self.tender_id, {
            'data': {
                "enquiryPeriod": {
                    "endDate": datetime.now(TZ).isoformat()
                },
                'tenderPeriod': {
                    'startDate': datetime.now(TZ).isoformat()
                }
            }
        })
        for _ in range(100):
            response = self.app.get('/recheck/' + self.tender_id)
            self.assertEqual(response.status, '200 OK')
            self.assertNotEqual(response.json, None)
            response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
            tender = response.json['data']
            if response.json['data']['status'] == 'active.tendering':
                break
            sleep(0.1)
        self.assertEqual(tender['status'], 'active.tendering')

    def test_wait_for_tenderPeriod(self):
        response = self.api.patch_json(self.app.app.registry.api_url + 'tenders/' + self.tender_id, {
            'data': {
                "enquiryPeriod": {
                    "endDate": datetime.now(TZ).isoformat()
                },
                'tenderPeriod': {
                    'startDate': (datetime.now(TZ) + timedelta(hours=1)).isoformat()
                }
            }
        })
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.enquiries')

    def test_set_auctionPeriod_jobs(self):
        now = datetime.now(TZ)
        self.api.patch_json(self.app.app.registry.api_url + 'tenders/' + self.tender_id, {
            'data': {
                "enquiryPeriod": {
                    "endDate": now.isoformat()
                },
                'tenderPeriod': {
                    'startDate': now.isoformat(),
                    'endDate': (now + timedelta(days=1)).isoformat()
                }
            }
        })
        for _ in range(100):
            self.app.app.registry.scheduler.start()
            response = self.app.get('/resync_all')
            self.assertEqual(response.status, '200 OK')
            self.assertNotEqual(response.json, None)
            response = self.app.get('/')
            self.app.app.registry.scheduler.shutdown()
            self.assertEqual(response.status, '200 OK')
            self.assertIn('jobs', response.json)
            self.assertEqual(len(response.json['jobs']), 2)
            if "recheck_{}".format(self.tender_id) in response.json['jobs']:
                break
        self.assertIn("recheck_{}".format(self.tender_id), response.json['jobs'])

        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)

        for _ in range(10):
            self.app.app.registry.scheduler.start()
            self.app.get('/resync_all')
            self.app.app.registry.scheduler.shutdown()

            response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
            tender = response.json['data']
            self.assertEqual(tender['status'], 'active.tendering')

            if self.initial_lots:
                self.assertIn('auctionPeriod', tender['lots'][0])
                if 'startDate' in tender['lots'][0]['auctionPeriod']:
                    break
            else:
                self.assertIn('auctionPeriod', tender)
                if 'startDate' in tender['auctionPeriod']:
                    break
        else:
            response = self.app.get('/resync/' + self.tender_id)
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.json, None)

        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.tendering')
        if self.initial_lots:
            self.assertIn('startDate', tender['lots'][0]['auctionPeriod'])
        else:
            self.assertIn('startDate', tender['auctionPeriod'])

    def test_set_auctionPeriod_nextday(self):
        now = datetime.now(TZ)
        response = self.api.patch_json(self.app.app.registry.api_url + 'tenders/' + self.tender_id, {
            'data': {
                "enquiryPeriod": {
                    "endDate": now.isoformat()
                },
                'tenderPeriod': {
                    'startDate': now.isoformat(),
                    'endDate': (now + timedelta(days=7 - now.weekday())).replace(hour=13).isoformat()
                }
            }
        })
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.tendering')
        response = self.app.get('/resync/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.tendering')
        if self.initial_lots:
            self.assertIn('auctionPeriod', tender['lots'][0])
            self.assertEqual(parse_date(tender['lots'][0]['auctionPeriod']['startDate'], TZ).weekday(), 1)
        else:
            self.assertIn('auctionPeriod', tender)
            self.assertEqual(parse_date(tender['auctionPeriod']['startDate'], TZ).weekday(), 1)
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        self.app.app.registry.scheduler.start()
        response = self.app.get('/')
        self.assertEqual(response.status, '200 OK')
        self.assertIn('jobs', response.json)
        self.assertIn('recheck_{}'.format(self.tender_id), response.json['jobs'])
        self.assertGreaterEqual(parse_date(response.json['jobs']["recheck_{}".format(self.tender_id)]).utctimetuple(), parse_date(tender['tenderPeriod']['endDate']).utctimetuple())
        self.assertLessEqual(parse_date(response.json['jobs']["recheck_{}".format(self.tender_id)]).utctimetuple(), (parse_date(tender['tenderPeriod']['endDate']) + timedelta(minutes=5)).utctimetuple())

    def test_set_auctionPeriod_skip_weekend(self):
        now = datetime.now(TZ)
        response = self.api.patch_json(self.app.app.registry.api_url + 'tenders/' + self.tender_id, {
            'data': {
                "enquiryPeriod": {
                    "endDate": now.isoformat()
                },
                'tenderPeriod': {
                    'startDate': now.isoformat(),
                    'endDate': (now + timedelta(days=5 - now.weekday())).isoformat()
                }
            }
        })
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.tendering')
        response = self.app.get('/resync/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.tendering')
        if self.initial_lots:
            self.assertIn('auctionPeriod', tender['lots'][0])
            self.assertEqual(parse_date(tender['lots'][0]['auctionPeriod']['startDate'], TZ).weekday(), 0)
        else:
            self.assertIn('auctionPeriod', tender)
            self.assertEqual(parse_date(tender['auctionPeriod']['startDate'], TZ).weekday(), 0)

    def test_set_auctionPeriod_skip_holidays(self):
        now = datetime.now(TZ)
        today = now.date()
        for i in range(10):
            date = today + timedelta(days=i)
            self.app.post('/calendar/' + date.isoformat())
        calendar = self.app.get('/calendar').json
        response = self.api.patch_json(self.app.app.registry.api_url + 'tenders/' + self.tender_id, {
            'data': {
                "enquiryPeriod": {
                    "endDate": now.isoformat()
                },
                'tenderPeriod': {
                    'startDate': now.isoformat(),
                    'endDate': (now + timedelta(days=1)).isoformat()
                }
            }
        })
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.tendering')
        response = self.app.get('/resync/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.tendering')
        if self.initial_lots:
            self.assertIn('auctionPeriod', tender['lots'][0])
            auctionPeriodstart = parse_date(tender['lots'][0]['auctionPeriod']['startDate'], TZ)
        else:
            self.assertIn('auctionPeriod', tender)
            auctionPeriodstart = parse_date(tender['auctionPeriod']['startDate'], TZ)
        self.assertNotIn(auctionPeriodstart.date().isoformat(), calendar)
        self.assertTrue(auctionPeriodstart.date() > date)

    def test_set_auctionPeriod_today(self):
        now = datetime.now(TZ)
        response = self.api.patch_json(self.app.app.registry.api_url + 'tenders/' + self.tender_id, {
            'data': {
                "enquiryPeriod": {
                    "endDate": now.isoformat()
                },
                'tenderPeriod': {
                    'startDate': now.isoformat(),
                    'endDate': (now + timedelta(days=7 - now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
                }
            }
        })
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.tendering')
        response = self.app.get('/resync/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.tendering')
        if self.initial_lots:
            self.assertIn('auctionPeriod', tender['lots'][0])
            self.assertEqual(parse_date(tender['lots'][0]['auctionPeriod']['startDate'], TZ).weekday(), 0)
        else:
            self.assertIn('auctionPeriod', tender)
            self.assertEqual(parse_date(tender['auctionPeriod']['startDate'], TZ).weekday(), 0)

    def test_switch_to_unsuccessful(self):
        response = self.api.patch_json(self.app.app.registry.api_url + 'tenders/' + self.tender_id, {
            'data': {
                "enquiryPeriod": {
                    "endDate": datetime.now(TZ).isoformat()
                },
                'tenderPeriod': {
                    'startDate': datetime.now(TZ).isoformat(),
                    "endDate": datetime.now(TZ).isoformat()
                }
            }
        })
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.tendering')
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'unsuccessful')


class TenderLotTest(TenderTest):
    initial_lots = test_lots


class TenderTest2(BaseTenderWebTest):
    scheduler = False
    initial_data = test_tender_data_quick
    initial_bids = test_bids[:1]

    def test_switch_to_qualification(self):
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.qualification')

    def test_switch_to_unsuccessful(self):
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.qualification')
        self.assertIn('awards', tender)
        award = tender['awards'][0]
        response = self.api.patch_json(self.app.app.registry.api_url + 'tenders/' + self.tender_id + '/awards/' + award['id'], {"data": {"status": "unsuccessful"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertNotEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.awarded')
        tender = self.api_db.get(self.tender_id)
        tender['awards'][0]['complaintPeriod']['endDate'] = datetime.now(TZ).isoformat()
        self.api_db.save(tender)
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'unsuccessful')


class TenderLotTest2(TenderTest2):
    initial_lots = test_lots


class TenderTest3(BaseTenderWebTest):
    scheduler = False
    initial_data = test_tender_data_quick
    initial_bids = test_bids

    def test_switch_to_auction(self):
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.auction')

    def test_reschedule_auction(self):
        response = self.app.get('/recheck/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.auction')
        if self.initial_lots:
            self.assertNotIn('auctionPeriod', tender)
            self.assertIn('auctionPeriod', tender['lots'][0])
            self.assertIn('shouldStartAfter', tender['lots'][0]['auctionPeriod'])
            self.assertNotIn('startDate', tender['lots'][0]['auctionPeriod'])
            self.assertGreater(tender['lots'][0]['auctionPeriod']['shouldStartAfter'], tender['lots'][0]['auctionPeriod'].get('startDate'))
        else:
            self.assertIn('auctionPeriod', tender)
            self.assertIn('shouldStartAfter', tender['auctionPeriod'])
            self.assertNotIn('startDate', tender['auctionPeriod'])
            self.assertGreater(tender['auctionPeriod']['shouldStartAfter'], tender['auctionPeriod'].get('startDate'))

        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.auction')

        response = self.app.get('/resync/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        tender = self.api_db.get(self.tender_id)
        if self.initial_lots:
            self.assertIn('auctionPeriod', tender['lots'][0])
            auctionPeriod = tender['lots'][0]['auctionPeriod']['startDate']
            tender['lots'][0]['auctionPeriod']['startDate'] = (datetime.now(TZ) - timedelta(hours=1)).isoformat()
        else:
            self.assertIn('auctionPeriod', tender)
            auctionPeriod = tender['auctionPeriod']['startDate']
            tender['auctionPeriod']['startDate'] = (datetime.now(TZ) - timedelta(hours=1)).isoformat()
        self.api_db.save(tender)

        response = self.api.get(self.app.app.registry.api_url + 'tenders/' + self.tender_id)
        tender = response.json['data']
        self.assertEqual(tender['status'], 'active.auction')
        if self.initial_lots:
            self.assertNotIn('auctionPeriod', tender)
            self.assertIn('auctionPeriod', tender['lots'][0])
            self.assertIn('shouldStartAfter', tender['lots'][0]['auctionPeriod'])
            self.assertIn('startDate', tender['lots'][0]['auctionPeriod'])
            self.assertGreater(tender['lots'][0]['auctionPeriod']['shouldStartAfter'], tender['lots'][0]['auctionPeriod'].get('startDate'))
        else:
            self.assertIn('auctionPeriod', tender)
            self.assertIn('shouldStartAfter', tender['auctionPeriod'])
            self.assertIn('startDate', tender['auctionPeriod'])
            self.assertGreater(tender['auctionPeriod']['shouldStartAfter'], tender['auctionPeriod'].get('startDate'))

        response = self.app.get('/resync/' + self.tender_id)
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json, None)
        tender = self.api_db.get(self.tender_id)
        if self.initial_lots:
            self.assertIn('auctionPeriod', tender['lots'][0])
            self.assertGreater(tender['lots'][0]['auctionPeriod']['startDate'], auctionPeriod)
        else:
            self.assertIn('auctionPeriod', tender)
            self.assertGreater(tender['auctionPeriod']['startDate'], auctionPeriod)


class TenderLotTest3(TenderTest3):
    initial_lots = test_lots


class TenderTest4(TenderTest3):
    sandbox = True


class TenderLotTest4(TenderTest4):
    initial_lots = test_lots


class TenderPlanning(BaseWebTest):
    scheduler = False

    def test_auction_quick_planning(self):
        now = datetime.now(TZ)
        auctionPeriodstartDate = planning_auction(test_tender_data_test_quick, now, self.db, True)[0]
        self.assertTrue(now < auctionPeriodstartDate < now + timedelta(hours=1))

    def test_auction_planning_overlow(self):
        now = datetime.now(TZ)
        res = planning_auction(test_tender_data_test_quick, now, self.db)[0]
        startDate = res.date()
        count = 0
        while startDate == res.date():
            count += 1
            res = planning_auction(test_tender_data_test_quick, now, self.db)[0]
        self.assertEqual(count, 100)

    def test_auction_planning_free(self):
        now = datetime.now(TZ)
        res = planning_auction(test_tender_data_test_quick, now, self.db)[0]
        startDate, startTime = res.date(), res.time()
        free_slot(self.db, "plantest_{}".format(startDate.isoformat()), res, "")
        res = planning_auction(test_tender_data_test_quick, now, self.db)[0]
        self.assertEqual(res.time(), startTime)

    def test_auction_planning_buffer(self):
        some_date = datetime(2015, 9, 21, 6, 30)
        date = some_date.date()
        ndate = (some_date + timedelta(days=1)).date()
        res = planning_auction(test_tender_data_test_quick, some_date, self.db)[0]
        self.assertEqual(res.date(), date)
        some_date = some_date.replace(hour=10)
        res = planning_auction(test_tender_data_test_quick, some_date, self.db)[0]
        self.assertNotEqual(res.date(), date)
        self.assertEqual(res.date(), ndate)
        some_date = some_date.replace(hour=16)
        res = planning_auction(test_tender_data_test_quick, some_date, self.db)[0]
        self.assertNotEqual(res.date(), date)
        self.assertEqual(res.date(), ndate)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SimpleTest))
    suite.addTest(unittest.makeSuite(TenderLotTest))
    suite.addTest(unittest.makeSuite(TenderLotTest2))
    suite.addTest(unittest.makeSuite(TenderLotTest3))
    suite.addTest(unittest.makeSuite(TenderLotTest4))
    suite.addTest(unittest.makeSuite(TenderPlanning))
    suite.addTest(unittest.makeSuite(TenderTest))
    suite.addTest(unittest.makeSuite(TenderTest2))
    suite.addTest(unittest.makeSuite(TenderTest3))
    suite.addTest(unittest.makeSuite(TenderTest4))
    suite.addTest(unittest.makeSuite(TendersTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite', exit=False)
