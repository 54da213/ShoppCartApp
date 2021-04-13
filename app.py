# -*- coding: utf-8 -*-
import os
from src.object import ReadCase, HandlerCase, Goods, DiscountController, OfferVolumeController, PayController


def app(CASE_FILE_NAME):
    caseGroup = ReadCase(CASE_FILE_NAME)
    discountGroup, goodsGroup, payDate, offerVolumeGroup = HandlerCase(caseGroup)
    # 批量实例化商品对象
    goodsIter = iter(goodsGroup)
    goodsObjectGroup = [Goods(goods) for goods in goodsIter]
    discountObject = DiscountController(discountGroup)
    offerVolumeObject = OfferVolumeController(offerVolumeGroup)

    payCtro = PayController(discountObject, offerVolumeObject, payDate)
    print(payCtro.pay(goodsObjectGroup))


if __name__ == '__main__':
    CASE_PATH = r"./case/"
    caseFileGroup = sorted(os.listdir(CASE_PATH))
    for case in caseFileGroup:
        caseName = os.path.join(CASE_PATH, case)
        app(caseName)
