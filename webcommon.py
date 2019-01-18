from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from ticenum import Locator, EcType

test_driver = None


def get_driver():
    global test_driver
    if not test_driver:
        test_driver = webdriver.Chrome()
    return test_driver


def get_object_by_id(element_id, wait_time=5, method=EcType.VISIBLE, driver=None):
    return get_object_by_locator(Locator.ID.value, element_id, wait_time, method, driver)


def get_object_by_xpath(element_xpath, wait_time=5, method=EcType.VISIBLE, driver=None):
    return get_object_by_locator(Locator.XPATH.value, element_xpath, wait_time, method, driver)


def get_object_by_name(element_name, wait_time=5, method=EcType.VISIBLE, driver=None):
    return get_object_by_locator(Locator.NAME.value, element_name, wait_time, method, driver)


def get_object_by_class(class_name, wait_time=5, method=EcType.VISIBLE, driver=None):
    return get_object_by_locator(Locator.CLASS.value, class_name, wait_time, method, driver)


def get_object_by_css(css, wait_time=5, method=EcType.VISIBLE, driver=None):
    return get_object_by_locator(Locator.CSS.value, css, wait_time, method, driver)


def get_object_by_locator(locator, value, wait_time=5, method=EcType.VISIBLE, driver=None):
    """
    :param locator: the value are defined in ticnum Locator value, should be like "ticenum.Locator.ID.value"
    :param value: this value is the element ID or xpath or classname etc..
    :param wait_time:
    :param method:
    :param driver: if it's None, means driver = ticWebDriver.
    :param log: true means if timeout then log steps and take screenshot
    :return: element, or None
    """
    driver = get_driver() if driver is None else driver
    if wait_time >= 0:
        return wait_element(locator, value, wait_time, method, driver)
    else:
        return wait_until_not_element(locator, value, wait_time, method, driver)


def wait_element(locator, value, wait_time, method, driver):
    try:
        waits = WebDriverWait(driver, wait_time)
        if method == EcType.VISIBLE:
            element = waits.until(EC.visibility_of_element_located((locator, value)))
        elif method == EcType.ALL_PRESENCE:
            element = waits.until(EC.presence_of_all_elements_located((locator, value)))
        elif method == EcType.PRESENCE:
            element = waits.until(EC.presence_of_element_located((locator, value)))
        elif method == EcType.CLICK:
            element = waits.until(EC.element_to_be_clickable((locator, value)))
        elif method == EcType.ALL_VISIBLE:
            element = waits.until(EC.visibility_of_any_elements_located((locator, value)))
        elif method == EcType.INVISIBLE:
            element = waits.until(EC.invisibility_of_element_located((locator, value)))
        else:
            element = waits.until(EC.visibility_of_element_located((locator, value)))
    except Exception as e:
        return None
    else:
        return element


def wait_until_not_element(locator, value, wait_time, method, driver):
    wait_time = abs(wait_time)
    try:
        waits = WebDriverWait(driver, wait_time)
        if method == EcType.VISIBLE:
            waits.until_not(EC.visibility_of_element_located((locator, value)))
        elif method == EcType.PRESENCE:
            waits.until_not(EC.presence_of_element_located((locator, value)))
        elif method == EcType.CLICK:
            waits.until_not(EC.element_to_be_clickable((locator, value)))
        elif method == EcType.INVISIBLE:
            waits.until_not(EC.invisibility_of_element_located((locator, value)))
        elif method == EcType.ALL_PRESENCE:
            waits.until_not(EC.presence_of_all_elements_located((locator, value)))
        elif method == EcType.ALL_VISIBLE:
            waits.until_not(EC.visibility_of_any_elements_located((locator, value)))
        else:
            waits.until_not(EC.visibility_of_element_located((locator, value)))
    except Exception as e:
        return wait_element(locator, value, 0, method, driver)
    else:
        return None
