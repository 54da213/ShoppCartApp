import re
import time

# 定义商品菜单
GOODS_MENU = {
    "电子": ["ipad", "iphone", "显示器", "笔记本电脑", "键盘"],
    "食品": ["面包", "饼干", "蛋糕", "牛肉", "鱼", "蔬菜"],
    "日用品": ["餐巾纸", "收纳箱", "咖啡杯", "雨伞"],
    "酒类": ["啤酒", "白酒", "伏特加"]
}


class OfferVolumeController(object):
    def __init__(self, offerVolumeGroup):
        self.isEmpty = True
        if offerVolumeGroup:
            self.isEmpty = False

        self._END_DATE_INDEX = 0
        self._ACHIEVE_FEE_INDEX = 1
        self._RELIEF_FEE_INDEX = 2
        self._offerVolumeGroup = []
        self._endTime, self._achieveFee, self._reliefFee = 0, 0, 0  # 优惠到期时间;满足条件;减免金额

        # 清理转换源数据以便之后业务进行
        self._offerVolumeGroup = [
            [
                DatetoTime(info[self._END_DATE_INDEX].replace('.', '-')),
                int(info[self._ACHIEVE_FEE_INDEX]),
                int(info[self._RELIEF_FEE_INDEX])
            ]
            for info in offerVolumeGroup
        ]

    def query(self, fee, payTime: int) -> float:
        '''
        查询优惠方案
        注意:不管有无优惠方案均有结果返回 无优惠方案时优惠金额为0.00元
        :param fee: 商品总金额
        :param payTime: 结算日期
        :return: 优惠金额
        '''
        if self.isEmpty:
            return 0.00
        self._endTime, self._achieveFee, self._reliefFee = self._offerVolumeGroup[0]
        if payTime > self._endTime:
            return 0.00
        if fee < self._achieveFee:
            return 0.00
        return self._reliefFee


class DiscountController(object):
    def __init__(self, discountGroup):
        self.isEmpty = True
        self._DISCOUNT_DATE_INDEX = 0
        self._DISCOUNT_COEFFICIENT_INDEX = 1
        self._DISCOUNT_GOODS_TYPE_INDEX = 2
        if not discountGroup:
            return
        self.isEmpty = False
        self._discountGroup = []
        self.discountTime = 0
        for discountInfo in discountGroup:
            discountDate = DatetoTime(discountInfo[self._DISCOUNT_DATE_INDEX].replace('.', '-'))  # 数据清洗
            coefficient = float(discountInfo[self._DISCOUNT_COEFFICIENT_INDEX])
            discountGoosType = discountInfo[self._DISCOUNT_GOODS_TYPE_INDEX].replace(' ', '')
            self._discountGroup.append([discountDate, coefficient, discountGoosType])

    def query(self, goodsObject, payTime) -> float:
        '''
        查询商品是否具有促销信息
        注意:不管是否具有促销信息均有结果返回 无促销信息时返回折扣系数1.0
        :param goodsObject: 商品实例
        :param payTime: 结算日期(时间戳)
        :return: 折扣系数
        '''
        # 此类商品是否打折
        coefficient = 1.0  # 默认该商品没有促销折扣系数为1
        if self.isEmpty:
            return coefficient
        isDiscount = False
        for discount in self._discountGroup:
            if goodsObject.type != discount[self._DISCOUNT_GOODS_TYPE_INDEX]:
                continue
            if payTime != discount[self._DISCOUNT_DATE_INDEX]:
                continue
            coefficient = float(discount[self._DISCOUNT_COEFFICIENT_INDEX])  # 折扣系数
            isDiscount = True

        if not isDiscount:
            return coefficient
        return coefficient


class Goods(object):
    def __init__(self, goodInfo):
        self.n, self.name, self._price = goodInfo
        self._price = float(self._price)
        if self._price < 0.00:
            self._price = 0.00

        self.n = int(self.n)  # 合法性校验
        if self.n < 0:
            self.n = 0
        self.name = self.name.replace(' ', '')

        self.type = ""
        for goodsType, goodsTypeGroup in GOODS_MENU.items():  # 划分种类
            if self.name in goodsTypeGroup:
                self.type = goodsType
                break

    def SetPrice(self, setPrice: float):
        '''
        商品单价过滤器,验证单价是否合法,且重置单价
        :param setPrice: 新单价
        :return:
        '''
        if setPrice < 0:
            return
        self._price = float(setPrice)

    def GetPrice(self):
        return self._price

    def __add__(self, other):
        return self._price + other.GetPrice()

    def __radd__(self, other):
        return self._price + other


class PayController(object):
    def __init__(self, discountObject: DiscountController, offerVolumeObject: OfferVolumeController, paydate: list):
        self.payTime = DatetoTime("-".join(paydate))
        self._discountObject = discountObject
        self._offerVolumeObject = offerVolumeObject

    def pay(self, goodsObjectGroup: list) -> str:
        '''
        结算购物车商品计算总金额
        :param goodsObjectGroup:商品实例队列
        :return: 商品应付金额
        '''
        fee = 0.00
        for goodsObject in goodsObjectGroup:
            # 此类商品是否打折
            coefficient = self._discountObject.query(goodsObject, self.payTime)
            fee += goodsObject.GetPrice() * coefficient * goodsObject.n  # 单品总价 = 单价 * 折扣系数 * 数量

        relief = self._offerVolumeObject.query(fee, self.payTime)
        payable = fee - relief  # 应付 = 总价 - 优惠
        return "%.02f" % float(payable)


def ReadCase(fileName: str) -> list:
    '''
    读取测试用例文件
    :param fileName:
    :return:
    '''
    with open(fileName, "r",encoding="utf8") as f:
        caseTxt = f.readlines()
    return caseTxt


def DatetoTime(date: str) -> int:
    '''
    格式化日期转时间戳
    :param date:
    :return:
    '''
    return int(time.mktime(time.strptime(date, "%Y-%m-%d")))


def HandlerCase(caseLineGroup):
    '''
    根据不同数据特征提取相关数据,进入不同容器
    :param caseLineGroup:
    :return:
    '''
    discountGroup = []  # 促销信息
    goodsGroup = []  # 商品信息
    offerVolumeGroup = []  # 优惠信息
    payDateGroup = []  # 结算日期
    for line in caseLineGroup:
        if line.startswith('\n') or line.startswith(' '):
            continue
        line = line.replace('\n', '')

        discountInfo = line.split('|')  # 解析促销信息
        if len(discountInfo) >= 3:
            discountGroup.append([info.replace(' ', '') for info in discountInfo])
            continue
        goodsInfo = re.split('\*|:', line)  # 解析商品信息
        if len(goodsInfo) >= 3:
            goodsGroup.append(goodsInfo)
            continue

        offerVolumeInfo = line.split(' ')  # 解析优惠卷信息
        if len(offerVolumeInfo) >= 2:
            offerVolumeGroup.append(offerVolumeInfo)
            continue

        payDateGroup = line.split('.')  # 解析结算日期
        if len(payDateGroup) >= 3:
            continue
    return discountGroup, goodsGroup, payDateGroup, offerVolumeGroup
