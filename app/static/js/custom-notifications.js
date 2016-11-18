function flashNotification(message, type, from, align){
    if (type) {var type = type;} else {var type = "info";}
    if (type == "success") {var icon = "ti-check";}
    else if (type == "info") {var icon = "ti-info";}
    else {var icon = "ti-bell";}

	$.notify({
    	icon: icon,
    	message: message

    },{
        type: type,
        timer: 1000,
        placement: {
            from: from,
            align: align
        }
    });
}