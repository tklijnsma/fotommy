function submitFunction(prefix) {
    console.log("submitFunction called with prefix = " + prefix);
    document.getElementById(prefix + "form").submit();
    document.getElementById(prefix + "n_likes").innerHTML = parseInt(document.getElementById(prefix + "n_likes").innerHTML) + 1;

    var old_element = document.getElementById(prefix + "submit");
    var new_element = old_element.cloneNode(true);
    new_element.setAttribute("class", "fotommy-button fotommy-greybutton")
    old_element.parentNode.replaceChild(new_element, old_element);
    }

function disableCommentSubmit(prefix) {
    console.log("disableCommentSubmit called with prefix = " + prefix);
    var old_element = document.getElementById(prefix + "submit");
    var new_element = old_element.cloneNode(true);
    new_element.setAttribute("class", "fotommy-button fotommy-greybutton");
    new_element.disabled = true;
    new_element.innerHTML = "Sending...";
    old_element.parentNode.replaceChild(new_element, old_element);
    document.getElementById(prefix + "form").submit();
    }
