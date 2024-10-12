/* Project specific Javascript goes here. */
/* Project specific Javascript goes here. */
// This file is automatically compiled by Webpack, along with any other files
// present in this directory. You're encouraged to place your actual application logic in
// a relevant structure within app/javascript and only use these pack files to reference
// that code so it'll be compiled.
var availablePSs
$(document).ready(function() {
    var elementExists = document.getElementById("availableTags");
    if (elementExists) {
        var ps = "";
        var pscode = [];
        const availableTags = JSON.parse(document.getElementById('availableTags').textContent);
        const availablePSsArray = JSON.parse(document.getElementById('ps_list').textContent);
        var availablePSs = availablePSsArray.map(x => " ".concat(x[1]));
        var elementExists2 = document.getElementById("police_station_id");
        $("#police_station_id").empty();
        // console.log(elementExists2);

        if (elementExists2) {
            // console.log("ps selector is here");
            var options_for_ps = '<option value="' + "" + '">' + "" + '</option>';
            for (var i = 0; i < availablePSs.length; i++) {
                options_for_ps += '<option value="' + availablePSsArray[i][0] + '">' + availablePSsArray[i][1] + '</option>';

            }
            $("#police_station_id").append(options_for_ps);
            // console.log(elementExists2);
        }

        function split(val) {
            return val.split(/,\s*/);
        }

        function extractLast(term) {
            return split(term).pop();
        }

        $("#search_crime_mobs")
            // don't navigate away from the field on tab when selecting an item
            .bind("keydown", function(event) {
                if (event.keyCode === $.ui.keyCode.TAB &&
                    $(this).autocomplete("instance").menu.active) {
                    event.preventDefault();
                }
            })
            .autocomplete({
                minLength: 0,
                source: function(request, response) {
                    // delegate back to autocomplete, but extract the last term
                    response($.ui.autocomplete.filter(
                        availableMOBs, extractLast(request.term)));
                },
                focus: function() {
                    // prevent value inserted on focus
                    return false;
                },
                select: function(event, ui) {
                    var terms = split(this.value);
                    // remove the current input
                    terms.pop();
                    // add the selected item
                    terms.push(ui.item.value);
                    // add placeholder to get the comma-and-space at the end
                    terms.push("");
                    this.value = terms.join(", ");
                    return false;
                }
            });
        $("#search_criminal_mobs")
            // don't navigate away from the field on tab when selecting an item
            .bind("keydown", function(event) {
                if (event.keyCode === $.ui.keyCode.TAB &&
                    $(this).autocomplete("instance").menu.active) {
                    event.preventDefault();
                }
            })
            .autocomplete({
                minLength: 0,
                source: function(request, response) {
                    // delegate back to autocomplete, but extract the last term
                    response($.ui.autocomplete.filter(
                        availableMOBs, extractLast(request.term)));
                },
                focus: function() {
                    // prevent value inserted on focus
                    return false;
                },
                select: function(event, ui) {
                    var terms = split(this.value);
                    // remove the current input
                    terms.pop();
                    // add the selected item
                    terms.push(ui.item.value);
                    // add placeholder to get the comma-and-space at the end
                    terms.push("");
                    this.value = terms.join(", ");
                    return false;
                }
            });
        // tags
        $("#id_tags")
            // don't navigate away from the field on tab when selecting an item
            .bind("keydown", function(event) {
                if (event.keyCode === $.ui.keyCode.TAB &&
                    $(this).autocomplete("instance").menu.active) {
                    event.preventDefault();
                }
            })
            .autocomplete({
                minLength: 0,
                source: function(request, response) {
                    // delegate back to autocomplete, but extract the last term
                    response($.ui.autocomplete.filter(
                        availableTags, extractLast(request.term)));
                },
                focus: function() {
                    // prevent value inserted on focus
                    return false;
                },
                select: function(event, ui) {
                    var terms = split(this.value);
                    // remove the current input
                    terms.pop();
                    // add the selected item
                    terms.push(ui.item.value);
                    // add placeholder to get the comma-and-space at the end
                    terms.push("");
                    this.value = terms.join(", ");
                    return false;
                }
            });
        $("#search_criminal_tags")
            // don't navigate away from the field on tab when selecting an item
            .bind("keydown", function(event) {
                if (event.keyCode === $.ui.keyCode.TAB &&
                    $(this).autocomplete("instance").menu.active) {
                    event.preventDefault();
                }
            })
            .autocomplete({
                minLength: 0,
                source: function(request, response) {
                    // delegate back to autocomplete, but extract the last term
                    response($.ui.autocomplete.filter(
                        availableTags, extractLast(request.term)));
                },
                focus: function() {
                    // prevent value inserted on focus
                    return false;
                },
                select: function(event, ui) {
                    var terms = split(this.value);
                    // remove the current input
                    terms.pop();
                    // add the selected item
                    terms.push(ui.item.value);
                    // add placeholder to get the comma-and-space at the end
                    terms.push("");
                    this.value = terms.join(", ");
                    return false;
                }
            });
        // }
        if ($("#crime_classification_list").length > 0) {
            $("#crime_classification_list")
                // don't navigate away from the field on tab when selecting an item
                .bind("keydown", function(event) {
                    if (event.keyCode === $.ui.keyCode.TAB &&
                        $(this).autocomplete("instance").menu.active) {
                        event.preventDefault();
                    }
                })
                .autocomplete({
                    minLength: 0,
                    source: function(request, response) {
                        // delegate back to autocomplete, but extract the last term
                        response($.ui.autocomplete.filter(
                            availableTags, extractLast(request.term)));
                    },
                    focus: function() {
                        // prevent value inserted on focus
                        return false;
                    },
                    select: function(event, ui) {
                        var terms = split(this.value);
                        // remove the current input
                        terms.pop();
                        // add the selected item
                        terms.push(ui.item.value);
                        // add placeholder to get the comma-and-space at the end
                        terms.push("");
                        this.value = terms.join(", ");
                        return false;
                    }
                });

            $("#crime_MOB_list")
                // don't navigate away from the field on tab when selecting an item
                .bind("keydown", function(event) {
                    if (event.keyCode === $.ui.keyCode.TAB &&
                        $(this).autocomplete("instance").menu.active) {
                        event.preventDefault();
                    }
                })
                .autocomplete({
                    minLength: 0,
                    source: function(request, response) {
                        // delegate back to autocomplete, but extract the last term
                        response($.ui.autocomplete.filter(
                            availableMOBs, extractLast(request.term)));
                    },
                    focus: function() {
                        // prevent value inserted on focus
                        return false;
                    },
                    select: function(event, ui) {
                        var terms = split(this.value);
                        // remove the current input
                        terms.pop();
                        // add the selected item
                        terms.push(ui.item.value);
                        // add placeholder to get the comma-and-space at the end
                        terms.push("");
                        this.value = terms.join(", ");
                        return false;
                    }
                });
        }
        if ($("#criminal_classification_list").length > 0) {
            $("#criminal_classification_list")
                // don't navigate away from the field on tab when selecting an item
                .bind("keydown", function(event) {
                    if (event.keyCode === $.ui.keyCode.TAB &&
                        $(this).autocomplete("instance").menu.active) {
                        event.preventDefault();
                    }
                })
                .autocomplete({
                    minLength: 0,
                    source: function(request, response) {
                        // delegate back to autocomplete, but extract the last term
                        response($.ui.autocomplete.filter(
                            availableTags, extractLast(request.term)));
                    },
                    focus: function() {
                        // prevent value inserted on focus
                        return false;
                    },
                    select: function(event, ui) {
                        var terms = split(this.value);
                        // remove the current input
                        terms.pop();
                        // add the selected item
                        terms.push(ui.item.value);
                        // add placeholder to get the comma-and-space at the end
                        terms.push("");
                        this.value = terms.join(", ");
                        return false;
                    }
                });


        }
        (function($) {
            $.widget("custom.combobox", {
                _create: function() {
                    this.wrapper = $("<span>")
                        .addClass("custom-combobox")
                        .insertAfter(this.element);

                    this.element.hide();
                    this._createAutocomplete();
                    // this._createShowAllButton();
                },

                _createAutocomplete: function() {
                    var selected = this.element.children(":selected"),
                        value = selected.val() ? selected.text() : "";

                    this.input = $("<input>")
                        .appendTo(this.wrapper)
                        .val(value)
                        .attr("title", "")
                        .addClass("custom-combobox-input ui-widget ui-widget-content ui-state-default ui-corner-left form-control input-lg")
                        .autocomplete({
                            delay: 0,
                            minLength: 0,
                            source: $.proxy(this, "_source")
                        })
                        .tooltip({
                            tooltipClass: "ui-state-highlight"
                        });

                    this._on(this.input, {
                        autocompleteselect: function(event, ui) {
                            ui.item.option.selected = true;
                            this._trigger("select", event, {
                                item: ui.item.option
                            });

                            if ($("#psquery").length > 0) {
                                pscode.push(ui.item.option.value);
                                ps = ps + ui.item.option.text + "</br>";

                                if ($("#id_ps_list").length > 0) {
                                    document.getElementById("id_ps_list").value = pscode;
                                } else if ($("#criminal_search_police_stations").length > 0) {
                                    document.getElementById("criminal_search_police_stations").value = pscode;
                                } else {
                                    alert($("#id_ps_list").length);
                                    document.getElementById("criminal_ps_op").value = pscode;
                                }
                                document.getElementById("psquery").innerHTML = ps;
                                return false;
                            }


                            if ($("#crime_classification_list").length > 0) {
                                document.getElementById("crime_police_station_id").value = ui.item.option.value;
                            }

                        },

                        autocompletechange: "_removeIfInvalid"
                    });
                },

                _createShowAllButton: function() {
                    var input = this.input,
                        wasOpen = false;

                    $("<a>")
                        .attr("tabIndex", -1)
                        .attr("title", "Show All Items")
                        .tooltip()
                        .appendTo(this.wrapper)
                        .button({
                            icons: {
                                primary: "ui-icon-triangle-1-s"
                            },
                            text: false
                        })
                        .removeClass("ui-corner-all")
                        .addClass("custom-combobox-toggle ui-corner-right")
                        .mousedown(function() {
                            wasOpen = input.autocomplete("widget").is(":visible");
                        })
                        .click(function() {
                            input.focus();

                            // Close if already visible
                            if (wasOpen) {
                                return;
                            }

                            // Pass empty string as value to search for, displaying all results
                            input.autocomplete("search", "");
                        });
                },

                _source: function(request, response) {
                    var matcher = new RegExp($.ui.autocomplete.escapeRegex(request.term), "i");
                    response(this.element.children("option").map(function() {
                        var text = $(this).text();
                        if (this.value && (!request.term || matcher.test(text)))
                            return {
                                label: text,
                                value: text,
                                option: this
                            };
                    }));
                },

                _removeIfInvalid: function(event, ui) {

                    // Selected an item, nothing to do
                    if (ui.item) {
                        return;
                    }

                    // Search for a match (case-insensitive)
                    var value = this.input.val(),
                        valueLowerCase = value.toLowerCase(),
                        valid = false;
                    this.element.children("option").each(function() {
                        if ($(this).text().toLowerCase() === valueLowerCase) {
                            this.selected = valid = true;
                            return false;
                        }
                    });

                    // Found a match, nothing to do
                    if (valid) {
                        return;
                    }

                    // Remove invalid value
                    this.input
                        .val("")
                        .attr("title", value + " didn't match any item")
                        .tooltip("open");
                    this.element.val("");
                    this._delay(function() {
                        this.input.tooltip("close").attr("title", "");
                    }, 2500);
                    this.input.autocomplete("instance").term = "";
                },

                _destroy: function() {
                    this.wrapper.remove();
                    this.element.show();
                }

            });


        })(jQuery);

        $(function() {
            $("#police_station_id").combobox();

        });
        $(function() {
            $("#search_arrest_date").datepicker({
                dateFormat: "yy/mm/dd"
            });
        });
        $(function() {
            $("#search_c_dt").datepicker({
                dateFormat: "yy/mm/dd"
            });
        });
        $(function() {
            $("#crime_search_case_date").datepicker({
                dateFormat: "yy/mm/dd"
            });
        });
        $(function() {
            $("#crime_case_date").datepicker({
                dateFormat: "yy/mm/dd"
            });
        });
        $(function() {
            $("#id_case_date").datepicker({
                dateFormat: "yy-mm-dd"
            });
        });
        $('#id_min_date').datepicker({
            dateFormat: 'yy-mm-dd'
        });
        $('#id_max_date').datepicker({
            dateFormat: 'yy-mm-dd'
        });
        $(function() {
            $("#crime_news_sheet_cns_date").datepicker({
                dateFormat: "yy-mm-dd"
            });
        });
        $(function() {
            $("#id_dr_date").datepicker({
                dateFormat: "yy-mm-dd"
            });
        });


        $(function() {
            $('#id_advanced_search').change(function() {
                $('.advanced-search-fields').toggle(this.checked);
            }).change(); //ensure visible state matches initially
        });
        $(function() {
            $('#id_advanced_search_crime').change(function() {
                $('.basic-search-fields').toggle(!this.checked);
                $('.advanced-search-fields').toggle(this.checked);
            }).change(); //ensure visible state matches initially
        });

        $(function() {
            var conditionRow = $('.form-row-clone:not(:last)');
            conditionRow.find('.btn.add-form-row')
                .removeClass('btn-success').addClass('btn-danger')
                .removeClass('add-form-row').addClass('remove-form-row')
                .html('<i class="fa fa-trash-alt"></i>');
            return false;
        });
        $(function() {
            var conditionRow = $('.form_-row-clone:not(:last)');
            conditionRow.find('.btn.add-form_-row')
                .removeClass('btn-success').addClass('btn-danger')
                .removeClass('add-form_-row').addClass('remove-form_-row')
                .html('<i class="fa fa-trash-alt"></i>');
            return false;
        });
        $(function() {
            var ids = []
            $('#id_mark_adder').click(function() {
                new_id = $('#id_id_mark').val();
                ids.push(new_id);
                document.getElementById('id_combined_id_mark').value = ids.join("|");
                document.getElementById('combined_id_mark').innerHTML = ids.join(",");
                document.getElementById('id_id_mark').value = null;
            }); //ensure visible state matches initially
        });

        // $(function() {
        // $( "[id^='crime_involvements_attributes']" ).datepicker();
        // });
        $("#report_duplicate_criminals").click(function() {
            var report = $("#duplicate_criminals").val();
            var report_array = report.match(/\d+/g);
            var report_crim_id = [];
            $.each(report_array, function(index, value) {
                report_crim_id.push($("#" + value).data("crim"));
            });
            alert("Thanks for reporting");
            $.ajax({
                type: "POST",
                url: "/criminal_duplicates",
                data: {
                    criminal_duplicate: {
                        reported_dup: report_crim_id.toString()
                    }
                }
            });
        });


        // Let's check if the browser supports notifications
        if (!("Notification" in window)) {

        }

        // Let's check whether notification permissions have already been granted
        else if (Notification.permission === "granted") {
            // If it's okay let's create a notification

        }

        // Otherwise, we need to ask the user for permission
        else if (Notification.permission !== 'denied') {
            Notification.requestPermission(function(permission) {
                // If the user accepts, let's create a notification
                if (permission === "granted") {

                }
            });
        }

        // Finally, if the user has denied notifications and you
        // want to be respectful there is no need to bother them any more.
    };
});
// Above ends the old CCS js code
$(document).on('focus', "input[id$='date']", function() {
    selected_id = "#" + $(this).first().attr("id");

    $(selected_id).datepicker({
        dateFormat: 'yy-mm-dd'
    });
    $(selected_id).change(function() {
        $(selected_id).datepicker("destroy");
    });

});
$(document).on('focus', "input[id$='police_station_with_distt']", function() {
    selected_id = "#" + $(this).first().attr("id");
    $(selected_id).autocomplete({
        source: availablePSs,
        change: function(event, ui) {
            // This block of code ensures that values are restricted to list items
            if (ui.item == null) {
                event.currentTarget.value = '';
                event.currentTarget.focus();
            }
            // This block of code ensures that values are restricted to list items
            else {
                $(selected_id).autocomplete("destroy");
            }
        }

    });


});

// http://127.0.0.1:8000/graphs/network_of_criminal/3f83bd84-69bc-4efd-a720-01882bc4a8ed
// THIS IS PROBABLY USELESS
$(document).ready(function() {
    function getNodeByUUID(uuid) {
        return nodes.filter(
            function(node) {
                return node.id == uuid
            }
        );
    }
    var nodes = []
    var elementExists = document.getElementById("task_id");
    if (elementExists) {
        var task_id = elementExists.innerHTML;
        var myVar = setInterval(pollCeleryTask, 1000);
        var x = 0;

        function pollCeleryTask() {
            if (++x === 10) {
                clearInterval(myVar);
            }

            $.ajax({
                url: '/ajax/tasks/',
                // url: '{% url "graphs:check_ajax_task" task_id=task_id%}',
                data: {
                    'task_id': task_id
                },
                dataType: 'json',
                success: function(data) {
                    if (data.state == "SUCCESS") {
                        var result = JSON.parse(data.info)
                        var edges = result["relationships"]
                        edges.forEach(function(obj) {
                            obj.title = (obj.fir_named ? 'FIR-named ' : '') + (obj.suspected ? 'Suspected ' : '') + (obj.arrested ? 'Arrested ' : '') + (obj.arrest_date ? 'D.O.A. ' + obj.arrest_date : '') + (obj.absconding ? 'Absconding' : '') + (obj.chargesheeted ? 'Charge-sheeted ' : '') + (obj.convicted ? 'Convicted ' : '')
                        });
                        nodes = result["nodes"]
                        // document.getElementById("criminal_network_data").innerHTML = data.info;
                        var container = document.getElementById('mynetwork');
                        var data = {
                            nodes: nodes,
                            edges: edges,
                        };
                        var options = {
                            width: '1000px',
                            height: '1000px'
                        };
                        var network = new vis.Network(container, data, options);
                        clearInterval(myVar);
                        // displaying gist on select
                        network.on('click', function(properties) {
                            node = getNodeByUUID(properties.nodes[0]);
                            if (node[0].group == "Crime") {
                                $.ajax({
                                    url: '/ajax/crimes/',
                                    data: {
                                        'unique_id': properties.nodes[0]
                                    },
                                    dataType: 'json',
                                    success: function(data) {
                                        alert('Gist: ' + data.gist);
                                    },
                                });
                            }
                        });
                        // displaying gist on select -> end
                        // navigating on hold
                        network.on('hold', function(properties) {
                            node = getNodeByUUID(properties.nodes[0]);
                            if (node[0].group == "Crime") {
                                window.location.assign('/backend/crimes/' + properties.nodes[0])
                            } else {
                                window.location.assign('/graphs/criminals/' + properties.nodes[0])
                            }
                        });
                        //navigating on hold -> end
                    }
                }
            });
        }

    };
});


// (1)  Criminal Detail without background task
$(document).ready(function() {

    var nodes = []
    var elementExists = document.getElementById("mynetwork");
    if (elementExists) {
        var result = JSON.parse(document.getElementById('network').textContent);
        result = JSON.parse(result)
        var edges = result["relationships"]
        edges.forEach(function(obj) {
            obj.title = (obj.fir_named ? 'FIR-named ' : '') + (obj.suspected ? 'Suspected ' : '') + (obj.arrested ? 'Arrested ' : '') + (obj.arrest_date ? 'D.O.A. ' + obj.arrest_date : '') + (obj.absconding ? 'Absconding' : '') + (obj.chargesheeted ? 'Charge-sheeted ' : '') + (obj.convicted ? 'Convicted ' : '')
        });
        nodes = result["nodes"]
        var container = document.getElementById('mynetwork');
        var data = {
            nodes: nodes,
            edges: edges,
        };
        var options = {
            width: '1000px',
            height: '1000px'
        };
        var network = new vis.Network(container, data, options);
        // displaying gist on select
        function getNodeByUUID(uuid) {
            return nodes.filter(
                function(node) {
                    return node.id == uuid
                }
            );
        }
        network.on('click', function(properties) {
            node = getNodeByUUID(properties.nodes[0]);
            if (node[0].group == "Crime") {
                $.ajax({
                    url: '/ajax/crimes/',
                    data: {
                        'unique_id': properties.nodes[0]
                    },
                    dataType: 'json',
                    success: function(data) {
                        alert('Gist: ' + data.gist);
                    },
                });
            }
        });
        // displaying gist on select -> end
        // navigating on hold
        network.on('hold', function(properties) {
            node = getNodeByUUID(properties.nodes[0]);
            if (node[0].group == "Crime") {
                window.location.assign('/backend/crimes/' + properties.nodes[0])
            } else {
                window.location.assign('/graphs/criminals/' + properties.nodes[0])
            }
        });
        //navigating on hold -> end




    };
});
// redoing criminal  detail-> end


// (2) Criminal's Network
$(document).ready(function() {

    var nodes = []
    $('.get_network').on('click', function(event) {
        $("#id_network_criminals").empty();
        event.preventDefault();
        get_criminals();

        function get_criminals() {
            $.ajax({
                url: '/ajax/get_network_of_criminal/',
                // url: '{% url "graphs:check_ajax_task" task_id=task_id%}',
                data: {
                    'tags': $('#id_tags').val(),
                    // 'all_tags': $('#id_all_tags').prop("checked"),
                    'uuid': window.location.pathname.split("/")[3]
                },
                dataType: 'json',
                success: function(data) {
                    var criminals = data.criminal_network;
                    var option = '';
                    for (var i = 0; i < criminals.length; i++) {
                        option += '<option value="' + criminals[i][0] + '">' + criminals[i][1] + '</option>';
                    }
                    $('#id_network_criminals').append(option);

                }
            });
            $('#id_network_criminals').change(function() {
                $.ajax({
                    url: '/ajax/nodes_paths/',
                    // url: '{% url "graphs:check_ajax_task" task_id=task_id%}',
                    data: {
                        'start_node': window.location.pathname.split("/")[3],
                        'end_node': $(this).val()
                    },
                    dataType: 'json',
                    success: function(data) {
                        var result = JSON.parse(data.results)
                        var nodes = result["nodes"];

                        // console.log(result);
                        var edges = result["relationships"]
                        edges.forEach(function(obj) {
                            obj.title = (obj.fir_named ? 'FIR-named ' : '') + (obj.suspected ? 'Suspected ' : '') + (obj.arrested ? 'Arrested ' : '') + (obj.arrest_date ? 'D.O.A. ' + obj.arrest_date : '') + (obj.absconding ? 'Absconding' : '') + (obj.chargesheeted ? 'Charge-sheeted ' : '') + (obj.convicted ? 'Convicted ' : '')
                        });
                        nodes = result["nodes"]
                        // document.getElementById("criminal_network_data").innerHTML = data.info;
                        var container = document.getElementById('criminal_network');
                        var data = {
                            nodes: nodes,
                            edges: edges,
                        };
                        var options = {
                            width: '1000px',
                            height: '1000px'
                        };
                        var network = new vis.Network(container, data, options);
                        // displaying gist on select
                        network.on('click', function(properties) {
                            node = getNodeByUUID(properties.nodes[0]);
                            if (node[0].group == "Crime") {
                                $.ajax({
                                    url: '/ajax/crimes/',
                                    data: {
                                        'unique_id': properties.nodes[0]
                                    },
                                    dataType: 'json',
                                    success: function(data) {
                                        alert('Gist: ' + data.gist);
                                    },
                                });
                            }
                        });
                        // displaying gist on select -> end
                        // navigating on hold
                        function getNodeByUUID(uuid) {
                            return nodes.filter(
                                function(node) {
                                    return node.id == uuid
                                }
                            );
                        }
                        network.on('hold', function(properties) {
                            node = getNodeByUUID(properties.nodes[0]);
                            if (node[0].group == "Crime") {
                                window.location.assign('/backend/crimes/' + properties.nodes[0])
                            } else {
                                window.location.assign('/graphs/criminals/' + properties.nodes[0])
                            }
                        });
                        //navigating on hold -> end
                    }
                });



            });

        };
    });
});

// End => Criminal's Network


// (3) Criminal's PS Associates
$(document).ready(function() {

    var nodes = []
    $('.get_ps_network').on('click', function(event) {
        $(document).find('.spinner-border').toggle();
        $("#id_network_criminals_ps").empty();
        event.preventDefault();
        $.ajax({
            url: '/ajax/get_connected_criminals_of_ps_task_id/',
            data: {
                'uuid': $('#id_first_criminal').val(),
                'ps_with_distt': $('#id_police_station_with_distt').val(),
                'crime_type': $('#id_crime_type_0').val()
            },
            dataType: 'json',
            success: function(data) {
                // Get the task ID
                var task_id = data.task_id;
                // Get the criminal list
                get_criminals();
                var x = 0;

                function get_criminals() {
                    var myVar = setInterval(pollCeleryTask, 30000);

                    function pollCeleryTask() {
                        if (++x === 10) {
                            clearInterval(myVar);
                        }
                        $.ajax({
                            url: '/ajax/get_connected_criminals_of_ps/',
                            data: {
                                'task_id': task_id
                            },
                            dataType: 'json',
                            success: function(data) {
                                console.log("done");
                                if (data.state == "SUCCESS") {
                                    $(document).find('.spinner-border').remove();

                                    var criminals = data.info.criminal_network;

                                    if (criminals.length == 0) {
                                        alert("No connection found.");
                                    } else {
                                        var option = '';
                                        for (var i = 0; i < criminals.length; i++) {
                                            option += '<option value="' + criminals[i][0] + '">' + criminals[i][1] + '</option>';
                                        }
                                        $('#id_network_criminals_ps').append(option);
                                    }

                                    clearInterval(myVar);
                                }

                            }
                        });

                    };
                };
            }
        });

    });
    $('#id_network_criminals_ps').change(function() {
        $.ajax({
            url: '/ajax/nodes_single_path/',
            data: {
                'start_node': $('#id_first_criminal').val(),
                'end_node': $(this).val()
            },
            dataType: 'json',
            success: function(data) {
                var result = JSON.parse(data.results)


                nodes = result["nodes"];

                var edges = result["relationships"]
                edges.forEach(function(obj) {
                    obj.title = (obj.fir_named ? 'FIR-named ' : '') + (obj.suspected ? 'Suspected ' : '') + (obj.arrested ? 'Arrested ' : '') + (obj.arrest_date ? 'D.O.A. ' + obj.arrest_date : '') + (obj.absconding ? 'Absconding' : '') + (obj.chargesheeted ? 'Charge-sheeted ' : '') + (obj.convicted ? 'Convicted ' : '')
                });
                // document.getElementById("criminal_network_data").innerHTML = data.info;
                var container = document.getElementById('criminals_path');
                var data = {
                    nodes: nodes,
                    edges: edges,
                };
                var options = {
                    width: '1000px',
                    height: '1000px'
                };
                var network = new vis.Network(container, data, options);
                // displaying gist on select
                function getNodeByUUID(uuid) {
                    return nodes.filter(
                        function(node) {
                            return node.id == uuid
                        }
                    );
                }
                network.on('click', function(properties) {
                    node = getNodeByUUID(properties.nodes[0]);


                    if (node[0].group == "Crime") {
                        $.ajax({
                            url: '/ajax/crimes/',
                            data: {
                                'unique_id': properties.nodes[0]
                            },
                            dataType: 'json',
                            success: function(data) {
                                alert('Gist: ' + data.gist);
                            },
                        });
                    }
                });
                // displaying gist on select -> end
                // navigating on hold
                network.on('hold', function(properties) {
                    node = getNodeByUUID(properties.nodes[0]);
                    if (node[0].group == "Crime") {
                        window.location.assign('/backend/crimes/' + properties.nodes[0])
                    } else {
                        window.location.assign('/graphs/criminals/' + properties.nodes[0])
                    }
                });
                //navigating on hold -> end
            }
        });
    });
});



// End => Criminal's PS Associates



$(document).ready(function() {
    $('#clipboard').on('click', function(event) {
        var copyText = document.getElementById('criminal_uuid');
        var textArea = document.createElement("textarea");
        textArea.value = copyText.textContent;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        textArea.remove();
    });
});

$(document).ready(function() {
    $('.clipboard_search_results').on('click', function(event) {
        event.preventDefault()
        var copyText = this.previousElementSibling.textContent;
        var textArea = document.createElement("textarea");
        textArea.value = copyText;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        textArea.remove();
    });
});

// (4) Two Criminals' path
$(document).ready(function() {

    var nodes = []
    $('.get_connection').on('click', function(event) {
        event.preventDefault();
        get_criminals();

        function get_criminals() {
            if ($('#id_first_criminal_name').val() == "" || $('#id_first_criminal_name').val() == "That is not a correct ID for any criminal" || $('#id_second_criminal_name').val() == "" || $('#id_second_criminal_name').val() == "That is not a correct ID for any criminal") {
                alert("Please select two criminals first");
            } else {

                $.ajax({
                    url: '/ajax/nodes_single_path/',
                    data: {
                        'start_node': $('#id_first_criminal').val(),
                        'end_node': $('#id_second_criminal').val()
                    },
                    dataType: 'json',
                    success: function(data) {
                        if (data.results.length != 0) {
                            var result = JSON.parse(data.results)
                            nodes = result["nodes"];
                            nodes.forEach(function(obj) {});
                            var edges = result["relationships"]
                            edges.forEach(function(obj) {
                                obj.title = (obj.fir_named ? 'FIR-named ' : '') + (obj.suspected ? 'Suspected ' : '') + (obj.arrested ? 'Arrested ' : '') + (obj.arrest_date ? 'D.O.A. ' + obj.arrest_date : '') + (obj.absconding ? 'Absconding' : '') + (obj.chargesheeted ? 'Charge-sheeted ' : '') + (obj.convicted ? 'Convicted ' : '')
                            });
                            nodes = result["nodes"]
                            var container = document.getElementById('criminals_path');
                            var data = {
                                nodes: nodes,
                                edges: edges,
                            };
                            var options = {
                                width: '1000px',
                                height: '1000px'
                            };
                            var network = new vis.Network(container, data, options);
                            // displaying gist on select
                            function getNodeByUUID(uuid) {
                                return nodes.filter(
                                    function(node) {
                                        return node.id == uuid
                                    }
                                );
                            }
                            network.on('click', function(properties) {
                                node = getNodeByUUID(properties.nodes[0]);
                                if (node[0].group == "Crime") {
                                    $.ajax({
                                        url: '/ajax/crimes/',
                                        data: {
                                            'unique_id': properties.nodes[0]
                                        },
                                        dataType: 'json',
                                        success: function(data) {
                                            alert('Gist: ' + data.gist);
                                        },
                                    });
                                }
                            });
                            // displaying gist on select -> end
                            // navigating on hold
                            network.on('hold', function(properties) {
                                node = getNodeByUUID(properties.nodes[0]);
                                if (node[0].group == "Crime") {
                                    window.location.assign('/backend/crimes/' + properties.nodes[0])
                                } else {
                                    window.location.assign('/graphs/criminals/' + properties.nodes[0])
                                }
                            });
                            //navigating on hold -> end

                        } else {
                            alert('There is no connection');
                        }
                    }
                });

            };




        }
    });
});

$(document).ready(function() {
    $("#id_first_criminal").on("input", function() {
        if ($("#id_first_criminal").val().length == 36)
            $.ajax({
                url: '/ajax/get_criminal_name/',
                data: {
                    'uuid': this.value
                },
                dataType: 'json',
                success: function(data) {
                    dates = data.dates
                    console.log(dates)
                }
            })
    });



    $("#id_second_criminal").on("input", function() {
        if ($("#id_second_criminal").val().length == 36)
            $.ajax({
                url: '/ajax/get_criminal_name/',
                data: {
                    'uuid': this.value
                },
                dataType: 'json',
                success: function(data) {
                    name = data.name
                    labels = $("#id_second_criminal").labels();
                    labels[0].innerHTML = "<strong>" + name + "<strong>";
                    $("#id_second_criminal_name").val(name);

                }
            })
    });
});
// trans_ps_border_stats
$(document).ready(function() {
    $('#trans_ps_border_stats').on('change.bootstrapSwitch', function(e) {
        console.log(e.target.checked);
    });
})

// Merge duplicate criminals
$(document).ready(function() {
    var accepted_duplicates = []
    var list_of_suggested_duplicates = ""
    $('#merge_duplicate_criminals').on('click', function(event) {
        var merger_action_to_be_taken = $('#merger_action_to_be_taken').val()
        console.log(merger_action_to_be_taken);
        $.each($(".dup_id"), function( index, value ) {
  if (this.checked) {
    accepted_duplicates.push(value.value);
  }
  else {

  };
    });
   accepted_duplicates = accepted_duplicates.join(",")
console.log(accepted_duplicates) ;
 list_of_suggested_duplicates = document.getElementById('duplicate_criminals_uuid').innerHTML
console.log(list_of_suggested_duplicates) ;
$.ajax({
                url: '/ajax/merge_duplicate_criminals/',
                data: {
                    'merger_action_to_be_taken': merger_action_to_be_taken,
                    'list_of_suggested_duplicates':list_of_suggested_duplicates,
                    'accepted_duplicates':accepted_duplicates
                },
                dataType: 'json'

            });
window.location.reload();
    });


});


// Merge duplicate criminals from list
$(document).ready(function() {
var div = document.getElementById('criminals_from_uuid');
var elementExists = document.getElementById("floatingTextarea");
    if (elementExists) {
        $(document).on('keypress',function(e) {
    if(e.which == 13) {
        if (elementExists.value.split("\n").slice(-1)[0].length == 36 ){
            $.ajax({
                url: '/ajax/get_criminal_name/',
                data: {
                    'uuid': elementExists.value.split("\n").slice(-1)[0]
                },
                dataType: 'json',
                success: function(data) {
                    name = data.name
                    div.innerHTML += "<p><strong>" + name + "</strong></p>";
                    console.log(data.name)

                }
            })
        }
          else {
            alert("Improper UUID")
          }

    }
});
    }
  $('#merge_duplicate_criminals_by_list').on('click', function(event) {

   accepted_duplicates = elementExists.value.split("\n").join(",").slice(0,-1)
console.log(accepted_duplicates) ;
$.ajax({
                url: '/ajax/merge_duplicate_criminals/',
                data: {
                    'merger_action_to_be_taken': '1',
                    'accepted_duplicates':accepted_duplicates,
                    'list_of_suggested_duplicates':''
                },
                dataType: 'json'

            });
window.location.reload();
    });





});
// tag management
$(document).ready(function() {
    var list_of_tags = []
    $('#tag_management').on('click', function(event) {
        event.preventDefault
        var merger_action_to_be_taken = $('#merger_action_to_be_taken').val()
        console.log(merger_action_to_be_taken);
        $.each($(".tag_id"), function( index, value ) {
  if (this.checked) {
    list_of_tags.push(value.value);
  }
  else {

  };
    });
   list_of_tags = list_of_tags.join(",")
console.log(list_of_tags) ;
$.ajax({
                url: '/ajax/manage_tags/',
                data: {
                    'merger_action_to_be_taken': merger_action_to_be_taken,
                    'list_of_tags':list_of_tags
                },
                dataType: 'json'

            });
window.location.reload();
    });


});

// Merge matched criminals
$(document).ready(function() {
    var accepted_matches = []
    $('#merge_matched_criminals').on('click', function(event) {
        $.each($(".dup_id"), function( index, value ) {
  if (this.checked) {
    accepted_matches.push(value.value);
  }
  else {

  };
    });
   accepted_match = accepted_matches[0]

    elementExists = document.getElementById("searched_url");
     avatar_url = elementExists.innerHTML;

$.ajax({
                url: '/ajax/merge_matched_criminal/',
                data: {
                    'accepted_match':accepted_match,
                    'avatar_url':avatar_url
                },
                dataType: 'json',
                success: function(data) {
                    url = data.avatar_url;
                    console.log(data.avatar_url);
                    console.log(data.accepted_match);
                },
            });
window.location.assign('/graphs/criminals/' + accepted_match);
    });


});
