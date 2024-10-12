console.log('Raw ps_list:', document.getElementById('ps_list').textContent);
console.log('Parsed ps_list:', JSON.parse(document.getElementById('ps_list').textContent));
const availablePSsArray = JSON.parse(document.getElementById('ps_list').textContent);
console.log('availablePSsArray:', availablePSsArray);
var availablePSs = availablePSsArray.map(x=>" ".concat(x[1]));
function updateElementIndex(el, prefix, ndx) {
    var id_regex = new RegExp('(' + prefix + '-\\d+)');
    var replacement = prefix + '-' + ndx;
    if ($(el).attr("for")) $(el).attr("for", $(el).attr("for").replace(id_regex, replacement));
    if (el.id) el.id = el.id.replace(id_regex, replacement);
    if (el.name) el.name = el.name.replace(id_regex, replacement);
}
function cloneMore(selector, prefix) {
    var newElement = $(selector).clone(true);
    var total = $('#id_' + prefix + '-TOTAL_FORMS').val();
    newElement.find(':input:not([type=button]):not([type=submit]):not([type=reset])').each(function() {
        if ($(this).attr("class") != "btn btn-success add-form-row"){
        // alert($(this).attr("class"));
        var name = $(this).attr('name').replace('-' + (total-1) + '-', '-' + total + '-');
        var id = 'id_' + name;
        $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
    };
    });
    newElement.find('label').each(function() {
        var forValue = $(this).attr('for');
        if (forValue) {
          forValue = forValue.replace('-' + (total-1) + '-', '-' + total + '-');
          $(this).attr({'for': forValue});
        }
    });
    total++;
    $('#id_' + prefix + '-TOTAL_FORMS').val(total);
    $(selector).after(newElement);
    var conditionRow = $('.form-row-clone:not(:last)');
    conditionRow.find('.btn.add-form-row')
    .removeClass('btn-success').addClass('btn-danger')
    .removeClass('add-form-row').addClass('remove-form-row')
    .html('<i class="fa fa-trash-alt"></i>');
    return false;
}
function deleteForm(prefix, btn) {
    var total = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val());
    if (total > 1){
        btn.closest('.form-row-clone').remove();
        var forms = $('.form-row-clone');
        $('#id_' + prefix + '-TOTAL_FORMS').val(forms.length);
        for (var i=0, formCount=forms.length; i<formCount; i++) {
            $(forms.get(i)).find(':input').each(function() {
                updateElementIndex(this, prefix, i);
            });
        }
    }
    return false;
}
function cloneMore_(selector, prefix) {
    var newElement = $(selector).clone(true);
    var total = $('#id_' + prefix + '-TOTAL_FORMS').val();
    newElement.find(':input:not([type=button]):not([type=submit]):not([type=reset])').each(function() {
        if ($(this).attr("class") != "btn btn-success add-form_-row"){
        // alert($(this).attr("class"));
        var name = $(this).attr('name').replace('-' + (total-1) + '-', '-' + total + '-');
        var id = 'id_' + name;
        $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
    };
    });
    newElement.find('label').each(function() {
        var forValue = $(this).attr('for');
        if (forValue) {
          forValue = forValue.replace('-' + (total-1) + '-', '-' + total + '-');
          $(this).attr({'for': forValue});
        }
    });
    total++;
    $('#id_' + prefix + '-TOTAL_FORMS').val(total);
    $(selector).after(newElement);
    var conditionRow = $('.form_-row-clone:not(:last)');
    conditionRow.find('.btn.add-form_-row')
    .removeClass('btn-success').addClass('btn-danger')
    .removeClass('add-form_-row').addClass('remove-form_-row')
    .html('<i class="fa fa-trash-alt"></i>');
    return false;
}
function deleteForm_(prefix, btn) {
    var total = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val());
    if (total > 1){
        btn.closest('.form_-row-clone').remove();
        var forms = $('.form_-row-clone');
        $('#id_' + prefix + '-TOTAL_FORMS').val(forms.length);
        for (var i=0, formCount=forms.length; i<formCount; i++) {
            $(forms.get(i)).find(':input').each(function() {
                updateElementIndex(this, prefix, i);
            });
        }
    }
    return false;
}
$(document).on('click', '.add-form-row', function(e){
    e.preventDefault();
    cloneMore('.form-row-clone:last', 'form');
    return false;
});
$(document).on('click', '.remove-form-row', function(e){
    var deletion_power = document.getElementById('deletion_power')
    console.log(deletion_power.innerHTML);
    if (deletion_power.innerHTML == "True") {
    e.preventDefault();
    deleteForm('form', $(this));
}
    return false;
});
$(document).on('click', '.add-form_-row', function(e){
    e.preventDefault();
    cloneMore_('.form_-row-clone:last', 'address');
    return false;
});
$(document).on('click', '.remove-form_-row', function(e){
    var deletion_power = document.getElementById('deletion_power')
    console.log(deletion_power.innerHTML);
    if (deletion_power.innerHTML == "True") {
    e.preventDefault();
    deleteForm_('address', $(this));
}
    return false;
});
