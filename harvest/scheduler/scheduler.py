import time
from pytz import timezone
import os
from harvest.services.risky52d.main import  Risky52D
import logging
log = logging.getLogger(__name__)

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events

from harvest.tasks import nse_download as nd
from harvest.tasks import eod_download as eod_hist

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

indian_tz = timezone('Asia/Kolkata')
cron_mode = 'prod'
cr1 = None
cr2 = None
cr3 = None

# (year, month, day, hr, min, sec )
# testing 
if cron_mode == 'test':
  cr1 = ('*','*','*','*',0,0)
  cr2 = ('*','*','*','*','*','*/30')
  cr3 = ('*','*','1',0,0,0)
# production
elif cron_mode == 'prod':
  cr1 =  ('*','*','*',18,0,0)#('*','*','*','*','*',0)#
  cr2 = ('*','*','*',18,30,0)
  cr3 = ('*','*','1',0,0,0)#('*','*','*','*','*',0)

def nse_download():
    log.debug("downloading nse eod file")
    nd.execute()

def risky52_predict():
    log.debug("downloading nse eod file")
    Risky52D.predict()

def low52_train():
    log.debug("I am log.debuged at 00:00:00 on the last Sunday of every month!")
    # eod_hist.execute()
    # Risky52D.train()

scheduler.add_job(nse_download, 'cron', id='nse_download',year=cr1[0], month=cr1[1], day=cr1[2], hour=cr1[3], minute=cr1[4], second=cr1[5],timezone=indian_tz, coalesce=True, misfire_grace_time=300, replace_existing=True)
scheduler.add_job(risky52_predict, 'cron', id='risky52_predict',year=cr2[0], month=cr2[1], day=cr2[2], hour=cr2[3], minute=cr2[4], second=cr2[5],timezone=indian_tz, coalesce=True, misfire_grace_time=300 , replace_existing=True)
scheduler.add_job(low52_train,'cron', id='low52_train',year=cr3[0], month=cr3[1], day=cr3[2], hour=cr3[3], minute=cr3[4], second=cr3[5],timezone=indian_tz, coalesce=True, misfire_grace_time=300, replace_existing=True)

# def low52_train():
#     log.debug("I am log.debuged at 00:00:00 on the last Sunday of every month!")
#     eod_hist.execute()
#     low52_tr.execute()

scheduler.start()
print("Scheduler started!")

# from pytz import utc
# from datetime import datetime
# import time
# from pytz import timezone
# import os

# import logging
# log = logging.getLogger(__name__)

# from apscheduler.schedulers.background import BackgroundScheduler
# from django_apscheduler.jobstores import DjangoJobStore

# # If you want all scheduled jobs to use this store by default,
# # use the name 'default' instead of 'djangojobstore'.
# scheduler.add_jobstore(DjangoJobStore(), 'djangojobstore')

# from harvest.tasks import nse_download as nd
# from harvest.tasks import eod_download as eod_hist
# from harvest.strategy.low52d import train_strategy as low52_tr
# from harvest.strategy.low52d import predict_strategy as low52_pr

# jobstores = {
#     'default': SQLAlchemyJobStore(url='sqlite:///harvest/../../db/jobs.sqlite')
# }
# executors = {
#     'default': {'type': 'threadpool', 'max_workers': 20},
#     'processpool': ProcessPoolExecutor(max_workers=5)
# }
# job_defaults = {
#     'coalesce': False,
#     'max_instances': 3
# }
# scheduler = BackgroundScheduler()

# indian_tz = timezone('Asia/Kolkata')
# cron_mode = 'prod'
# cr1 = None
# cr2 = None
# cr3 = None

# # (year, month, day, hr, min, sec )
# # testing 
# if cron_mode == 'test':
# 	cr1 = ('*','*','*',18,0,0)
# 	cr2 = ('*','*','*','*','*','*/30')
# 	cr3 = ('*','*','1',0,0,0)
# # production
# elif cron_mode == 'prod':
# 	cr1 = ('*','*','*',18,0,0)
# 	cr2 = ('*','*','*',18,30,0)
# 	cr3 = ('*','*','1',0,0,0)

# #@scheduler.scheduled_job('cron', id='nse_download',year=cr1[0], month=cr1[1], day=cr1[2], hour=cr1[3], minute=cr1[4], second=cr1[5],timezone='Asia/Kolkata', coalesce=True, misfire_grace_time=300)
# def nse_download():
# 	log.debug("downloading nse eod file")
# 	nd.execute()

# #@scheduler.scheduled_job('cron', id='low52_predict',year=cr2[0], month=cr2[1], day=cr2[2], hour=cr2[3], minute=cr2[4], second=cr2[5],timezone='Asia/Kolkata', coalesce=True, misfire_grace_time=300)
# def low52_predict():
# 	log.debug("downloading nse eod file")
# 	low52_pr.execute()

# #@scheduler.scheduled_job('cron', id='low52_train',year=cr3[0], month=cr3[1], day=cr3[2], hour=cr3[3], minute=cr3[4], second=cr3[5],timezone='Asia/Kolkata', coalesce=True, misfire_grace_time=300)
# def low52_train():
#     log.debug("I am log.debuged at 00:00:00 on the last Sunday of every month!")
#     eod_hist.execute()
#     low52_tr.execute()


# def intialize():
# 	log.debug('adding jobs')
# 	scheduler.add_job(nse_download, 'cron', id='nse_download',year=cr1[0], month=cr1[1], day=cr1[2], hour=cr1[3], minute=cr1[4], second=cr1[5],timezone=indian_tz, coalesce=True, misfire_grace_time=300, replace_existing=True)
# 	scheduler.add_job(low52_predict, 'cron', id='low52_predict',year=cr2[0], month=cr2[1], day=cr2[2], hour=cr2[3], minute=cr2[4], second=cr2[5],timezone=indian_tz, coalesce=True, misfire_grace_time=300 , replace_existing=True)
# 	scheduler.add_job(low52_train,'cron', id='low52_train',year=cr3[0], month=cr3[1], day=cr3[2], hour=cr3[3], minute=cr3[4], second=cr3[5],timezone=indian_tz, coalesce=True, misfire_grace_time=300, replace_existing=True)

# 	log.debug('starting scheduler')
# 	scheduler.start()
# 	return scheduler



# scheduler.configure(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)


# if __name__ == '__main__':
# 	intialize()


# # try:
# # 	# This is here to simulate application activity (which keeps the main thread alive).
# # 	while True:
# # 		time.sleep(2)
# # except (KeyboardInterrupt, SystemExit):
# # 		# Not strictly necessary if daemonic mode is enabled but should be done if possible
# # 		scheduler.shutdown()

# # if __name__ == '__main__':
# #     scheduler = BackgroundScheduler()
# #     scheduler.add_job(tick, 'interval', seconds=3)
# #     scheduler.start()
# #     log.debug('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))