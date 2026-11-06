import time, logging
logger=logging.getLogger('django.request')
class RequestTimingMiddleware:
 def __init__(self,get_response): self.get_response=get_response
 def __call__(self,request):
  start=time.perf_counter(); response=self.get_response(request); elapsed=(time.perf_counter()-start)*1000
  response['X-Response-Time']=f'{elapsed:.2f}ms'
  logger.info('%s %s → %s (%.2f ms)',request.method,request.path,response.status_code,elapsed)
  return response
