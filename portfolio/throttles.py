from rest_framework.throttling import AnonRateThrottle
class CommentThrottle(AnonRateThrottle): scope='comment'
class ContactThrottle(AnonRateThrottle): scope='contact'
class LikeThrottle(AnonRateThrottle): scope='like'
