from __future__ import annotations
from typing import Any, List
from uuid import uuid4
from bson import ObjectId
from pydantic import BaseModel
from messages_chain import ChainModel
from aiogram.utils.callback_data import CallbackData

class CategoryModel(BaseModel):
    parent_id: str = 'root'
    id= ''
    name: str
    extra: Any | None = None
    description: List[ChainModel] = []
    subcategories:  List[str] = []

    class Config:
        arbitrary_types_allowed = True



class Button(BaseModel):
    """Button for Custom Buttons

    Args:
        callback - you can put own callbak instance, but it must countain id field
        id is id category
    """
    callback: CallbackData
    own_args: dict
    name: str

    class Config:
        arbitrary_types_allowed = True


class CustomButtonsModel(BaseModel):
    """CustomButtons

    controls: Set your buttons for control menu delete, edit  and others

    category: For main menu buttons with subcategories & pagination
    """

    contorls:  List[Button]| None = None
    category:  List[Button] | None = None



class MessageTextModel(BaseModel):

    debug: bool = False
    menu: str = "Hi, selecet category for something"
    error_menu: str = "Main Categories not found"
    error_found: str = "Category not found"
    get_name: str = "Send Name new category"
    get_description: str = "Now send me description (it's maybe chain message with media) of category or press button for save without"
    get_new_name: str = "Send new Name"
    get_new_description: str = "Send new Description"
    name_updated:str = "Name Updated !"
    description_updated:str = "Description Updated !"
    btn_save_description: str ="Save Description"
    error_updating: str = "Update didn't applied something went wrong, please try again, maybe you input incorrect symbols"
    gategory_saved: str = "Category successfully added"
    error_saving: str = "Category didn't saved something went wrong, please try again"
    save_subcategories: str = "Save Subcategories ?"
    save_subcategories_btn_yes: str= "Yes"
    save_subcategories_btn_no: str = "No"
    btn_control: str = "Control Categories"
    btn_cancel_delete:str = "Cancel deleting"
    deleted_with_subs: str = "Category deleted with subcotegories"
    deleted_without_subs: str = "Category deleted, but subcategories moving on one step upper"

