"""Этот модуль управляет заказами и блюдами"""
import time
import asyncio

from base_order import BaseOrder
from equipment import Equipment


class PizzaBotMain(object):
    """Это основной класс блока.
    Этот класс содержит информацию о том, какие блюда готовятся в текущий момент, содержит информацию о печах и
    показываает время работы коиска. После завешения заказа, он удаляется из self.current_orders_proceed
    """

    def __init__(self, equipment_data, recipes):
        self.equipment = Equipment(equipment_data)
        self.is_cooking_paused = False
        # все заказы за текущий сеанс работы, {id: BaseOrder}
        self.current_orders_proceed = {}
        # все неприготовленые блюда
        self.current_dishes_proceed = {}
        self.time_to_cook_all_dishes_left = 2300
        self.orders_requested_for_delivery = {}
        self.recipes = recipes

    def checking_order_for_double(self, new_order_id):
        """Этот метод проверяет есть ли уже заказ с таким ref id в обработке
        :return bool"""
        is_new_order = True if new_order_id not in self.current_orders_proceed.keys() else False
        return is_new_order

    async def get_order_content_from_db(self, new_order_id):
        """Этот метод вызывает процедуру 'Получи состав блюд в заказе' и возвращает словарь вида
        {"refid": new_order_id,
                     "dishes": [
                         {"dough": {"id":2},
                          "sauce": {"id": 2, "content": ((1, 5), (2, 25))},
                         "filling": {"id": 1, "content": ((6, 1), (4, 1), (6, 1), (9, 2))},
                         "additive":{"id": 7}},
                         {"dough": {"id":1},
                          "sauce": {"id": 3, "content": ((1, 5), (2, 25))},
                         "filling": {"id": 4, "content": ((6, 1), (4, 1), (6, 1), (9, 2))},
                         "additive":{"id": 1}},
                     ]
                     }
        """
        new_order = {"refid": new_order_id,
                     "dishes": [
                         {"dough": {"id":2},
                          "sauce": {"id": 2, "content": ((1, 5), (2, 25))},
                         "filling": {"id": 1, "content": ((6, 1), (4, 1), (6, 1), (9, 2))},
                         "additive":{"id": 7}},
                         {"dough": {"id":1},
                          "sauce": {"id": 3, "content": ((1, 5), (2, 25))},
                         "filling": {"id": 4, "content": ((6, 1), (4, 1), (6, 1), (9, 2))},
                         "additive":{"id": 1}},
                     ]
                     }
        return new_order

    def get_recipe_data(self, new_order):
        """Этот метод добавляет в данные о блюде параметры чейнов рецепта для конкретного ингредиента"""
        for dish in new_order["dishes"]:
            dish["dough"]["recipe"] = self.recipes["dough"]
            dish["sauce"]["recipe"] = self.recipes["sauce"]
            dish["filling"]["recipe"] = self.recipes["filling"]
            dish["additive"]["recipe"] = self.recipes["additive"]
            print("В блюдо добавили рецепт")

    def create_new_order(self, new_order):
        """Этот метод создает экземпляр класса Order и заносит его в словарь self.current_orders_proceed
        @:params:
        new_order - это словарь с блюдами, получаемый из БД в рамках метода get_order_content_from_db """

        try:
            # резервируем печи для заказа
            ovens_reserved = [self.equipment.oven_reserve() for dish in new_order["dishes"]]
            # создаем экземпляр класса заказа
            order = BaseOrder(new_order, ovens_reserved)
            print("Создан заказ", order)
            print("Блюда в заказе", order.dishes)
            if order:
                # если заказ создан успешно, помещаем его в словарь всех готовящихся заказов
                self.current_orders_proceed[order.ref_id] = order
                # перемещаем заказы в словарь всех готовящихся блюд
                self.fill_current_dishes_proceed(order)
        # придумать ошибки какие могут быть
        except ValueError:
            pass

    def fill_current_dishes_proceed(self, order):
        """ Добавляет блюда заказа в self.current_dishes_proceed
        @:param order: экземпляр класса заказ, созданный в self.create_new_order"""

        for dish in order.dishes:
            self.current_dishes_proceed[dish.id] = dish
    #
    # def total_cooking_update(self):
    #     pass
    #
    # async def cooking_pause_handler(self):
    #     print("Приостанавливаем работу")
    #     #Controllers.disable_qrcode_validator()
    #     #RBA.go_to_transport_position()
    #     await asyncio.sleep(10)
    #     pass
    #
    # async def dish_delivery(self):
    #     print("Cooking: Обрабатываем сообщение от контроллера")
    #     print("классное сообщение от контролера - ВЫДАЧА заказа",
    #     self.orders_requested_for_delivery.popitem())
    #     await asyncio.sleep(5)
    #     print("ВЫДАЧА заказа завершена")
    #     print(time.time())

    """Валиация qr кода
       входные данные: чек код заказа и номер пункта выдачи
       выходные данные: сообщение контроллеру, запускается выдача заказа, если он готов, выдача подарка, если произошла ошибка
       ORDER_STATUS = ["received", "cooking", "ready", "informed", "packed", "wait to delivery", "delivered", "closed",
                       "failed_to_be_cooked", "not_delivered"]
       добавить статус "time_is_up"
       """

    STATUS_FOR_CNTRL = {"ready": "заказ готов, скоро будет доставлен",
                        "failed_to_be_cooked": "не смогли приготовить",
                        "cooking": "находится в процессе готовки", "time_is_up": "время получения заказа истекло",
                        "delivered": "заказ уже получен", "not_found": "заказ не найден"}

    async def qr_code_alarm(self):
        """ Ожидаем получения qr кода от контроллера"""
        print("Мониторим есть ли запрос qr code")
        while True:
            # тут какая то классная команда контроллерам, ниже просто симуляция работы
            await asyncio.sleep(30)
            # {"ref_id": 12, "pickup": 1} взяты для примера
            self.check_order_status({"ref_id": 12, "pickup": 1})

    def check_order_status(self, params):
        """Этот метод проверяет, есть ли заказ с таким чек кодом в current_orders_proceed.
        Входные данные params: полученный от контроллера словарь с чек кодом заказа и окном выдачи
        "ref_id": int, "pickup": int"""
        order_check_code = params["ref_id"]
        pickup_point = params["pickup"]
        if order_check_code in self.current_orders_proceed:
            print("Валидный qr code")
            order_status = self.current_orders_proceed[order_check_code].status
            return self.order_status_handler(order_status, order_check_code)
        else:
            return self.status_to_cntrl("not found")

    def order_status_handler(self, order_status, order_check_code):
        """Этот метод анализирует статус и запускает обработчик отправляет значение контролеру"""
        if order_status == "ready":
            print("Валидный qr code, надо выдать заказ")
            self.orders_requested_for_delivery[order_check_code] = order_check_code
            return self.status_to_cntrl("ready")
        elif order_status == "packed" or order_status == "wait to delivery":
            return self.status_to_cntrl("ready")
        elif order_status == "cooking" or order_status == "received":
            return self.status_to_cntrl("cooking")
        elif order_status == "failed_to_be_cooked":
            self.present_delivery_handler()
            return self.status_to_cntrl("failed_to_be_cooked")
        else:
            return self.status_to_cntrl(order_status)

    async def status_to_cntrl(self, status_of_order):
        """Передает контроллу значение, на основании которого пользователю выводится информация о заказе"""
        print("контроллеру передано сообщение: ", self.STATUS_FOR_CNTRL[status_of_order])
        # обращеноие к контролу

    # не надо вызывать, поскольку постоянно идет проверка на наличие заказов в orders_requested_for_delivery
    # async def order_delivery_handler(self):
       # """Обрабатывает процедуру получения заказа - Настя"""
       # print("получение заказа")
       # pass

    async def present_delivery_handler(self):
        """Обрабатывает процедуру получения подарка"""
        print("получение подарка")
        pass
