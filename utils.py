def get_text_javascript(driver, ele):
    """Get text of the element using javascript
    This allows getting text even for hidden elements
    """
    return driver.execute_script("return arguments[0].textContent;", ele)