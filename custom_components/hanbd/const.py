"""Constants for hanbd."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "hanbd"
ATTRIBUTION = "Data provided by HANBD"

# API Configuration
API_BASE_URL = "http://hbd-server-america.hgl-zj.com"
API_TIMEOUT = 10

# API Endpoints
ENDPOINT_AUTHORIZE = "/oauth/memberAuthorize"
ENDPOINT_DEVICE_LIST = "/member/device/list"
ENDPOINT_DEVICE_OPERATE = "/member/device-operate/operate"
ENDPOINT_GET_DISTRICT = "/member/getDistrict"
ENDPOINT_MEMBER_GET = "/member/member/get"

# APK static RSA public key (X.509 SubjectPublicKeyInfo, Base64 DER)
APP_PUBLIC_KEY = (
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCAqmXUjriavgcHQug7Qr6hh5VEp"
    "MfAOZxtKpcjGGMXeaT+BsfSLcrbwsDnYsocVYt7lZIeYo6GeN8Ab7VLLxYJoXsqZV"
    "f+sApBqBi9m5+KkCUz+igerSwowWs27nTSRo3lW5KQpaa1X6CsJrrEINpfXO4uWAZL"
    "J0MhUnKYg5cDYwIDAQAB"
)
