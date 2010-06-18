#!/usr/bin/python
import service
import gdata
import gdata.auth

a = service.BuzzService()
a.SetOAuthInputParameters(gdata.auth.OAuthSignatureMethod.HMAC_SHA1,
                          consumer_key='anonymous',
                          consumer_secret='anonymous')
tok = a.FetchOAuthRequestToken()
print a.GenerateOAuthAuthorizationURL(request_token=tok)
raw_input('go authorize')
a.UpgradeToOAuthAccessToken(tok)
print a.GetActivityFeed(user='googlebuzz')
