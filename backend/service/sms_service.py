from alibabacloud_dypnsapi20170525.client import Client as Dypnsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dypnsapi20170525 import models as dypnsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from core.settings import settings


# 短信服务AliyunSmsService类
class AliyunSmsService:
    def __init__(self):
        # 构造函数，此处无初始化内容
        pass

    @staticmethod
    def create_client() -> Dypnsapi20170525Client:
        """
        使用凭据初始化账号Client
        :return: 阿里云大于短信Client实例
        :raises Exception: 初始化Client时可能抛出的异常
        """
        # 创建API调用配置对象并设置AccessKey
        config = open_api_models.Config(
            access_key_id=settings.ALIYUN_ACCESS_KEY,
            access_key_secret=settings.ALIYUN_SECRET_KEY,
        )
        # 设置短信服务的endpoint
        config.endpoint = "dypnsapi.aliyuncs.com"
        # 返回短信API的Client对象
        return Dypnsapi20170525Client(config)

    @staticmethod
    async def send_sms(phone: str, code: str) -> bool:
        """
        发送验证码短信的异步方法
        :param phone: 手机号（接收验证码的目标手机号）
        :param code: 验证码内容
        :return: 请求结果（JSON字符串），发生异常时返回None
        """
        # 创建短信服务的client
        client = AliyunSmsService.create_client()
        # 构造短信请求对象，包括签名、模板、模板参数、目标手机号等
        send_sms_verify_code_request = (
            dypnsapi_20170525_models.SendSmsVerifyCodeRequest(
                sign_name="速通互联验证码",  # 签名名称
                template_code="100001",  # 模板CODE
                template_param=f'{{"code":"{code}","min":"5"}}',  # 模板参数
                phone_number=phone,  # 接收验证码的手机号
            )
        )
        # 运行选项，可设置超时、重试等
        runtime = util_models.RuntimeOptions()
        try:
            # 异步调用发送验证码API
            resp = await client.send_sms_verify_code_with_options_async(
                send_sms_verify_code_request, runtime
            )
            print(resp)
            # 返回请求结果的JSON字符串
            return resp.body.success
        except Exception as error:
            # 异常处理：打印错误信息和诊断建议
            # 注意：实际生产环境应当有更完善的异常处理机制
            print(str(error))  # 错误消息
            print(error.data.get("Recommend"))  # 诊断建议
