from enum import Enum
from selenium.webdriver.common.by import By


class EcType(Enum):
    VISIBLE = 1
    INVISIBLE = 2
    PRESENCE = 3
    CLICK = 4
    ALERT = 5
    SELECT = 6
    ALL_PRESENCE = 7
    ALL_VISIBLE = 8


class Locator(Enum):
    ID = By.ID
    XPATH = By.XPATH
    NAME = By.NAME
    CLASS = By.CLASS_NAME
    TAG = By.TAG_NAME
    CSS = By.CSS_SELECTOR
    P_LINK = By.PARTIAL_LINK_TEXT
    LINK = By.LINK_TEXT
