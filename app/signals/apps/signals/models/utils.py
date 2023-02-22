# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2023 Gemeente Amsterdam


def upload_category_icon_to(instance, filename):
    """
    Will create the upload to structure for category icons.
    For example:
    - icons/categories/afval/icon.jpg (Parent category)
    - icons/categories/afval/asbest-accu/icon.jpg (Child category)
    """
    file_path = 'icons/categories'
    if instance.is_parent():
        file_path = f'{file_path}/{instance.slug}'
    else:
        file_path = f'{file_path}/{instance.parent.slug}/{instance.slug}'
    return f'{file_path}/{filename}'
