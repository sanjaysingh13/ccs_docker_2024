/* Project specific Javascript goes here. */
// This file is automatically compiled by Webpack, along with any other files
// present in this directory. You're encouraged to place your actual application logic in
// a relevant structure within app/javascript and only use these pack files to reference
// that code so it'll be compiled.
$(document).ready(function() {
    var csrf_exists = document.querySelector('[class=tbl_witnesses]');
    if (csrf_exists) {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        console.log(csrftoken)



        var buffer = "next"
        var elementExists = document.getElementById("trial_monitoring");
        if (elementExists) {
            const witnesses_json = JSON.parse(document.getElementById('witnesses_json').textContent)
            // console.log(witnesses_json[0]);
            //--->create data table > start
            var tbl = '';
            tbl += '<table class="table table-hover table-condensed table-responsive table-striped">'

            //--->create table header > start
            tbl += '<thead>';
            tbl += '<tr>';
            tbl += '<th>Particulars</th>';
            tbl += '<th>Dates of Examination</th>';
            tbl += '<th>Gist of Deposition </th>';
            tbl += '<th>Favourable (yes/no)</th>';
            tbl += '<th>Save</th>';
            tbl += '</tr>';
            tbl += '</thead>';
            //--->create table header > end


            //--->create table body > start
            tbl += '<tbody>';

            //--->create table body rows > start
            $.each(witnesses_json, function(index, val) {
                //loop through ajax row data
                var row_id = val['uuid'];
                tbl += '<tr row_id="' + row_id + '">';
                tbl += '<td ><div  edit_type="click" col_name="particulars">' + val['particulars'] + '</div></td>';
                tbl += '<td ><div class="row_data" edit_type="click" col_name="dates_of_examination">' + val['dates_of_examination'] + '</div></td>';
                tbl += '<td ><div class="row_data" edit_type="click" col_name="gist_of_deposition">' + val['gist_of_deposition'] + '</div></td>';
                tbl += '<td ><div class="row_data" edit_type="click" col_name="favourable">' + val['favourable'] + '</div></td>';

                //--->edit options > start
                tbl += '<td>';



                //only show this button if edit button is clicked
                tbl += '<span class="btn_save"><a href="#" class="btn btn-link"  row_id="' + row_id + '">Save</a></span>';


                tbl += '</td>';
                //--->edit options > end

                tbl += '</tr>';
            });

            //--->create table body rows > end

            tbl += '</tbody>';
            //--->create table body > end

            tbl += '</table>'
            //--->create data table > end

            //out put table data
            $(document).find('.tbl_witnesses').html(tbl);




            //--->make div editable > start
            $(document).on('click', '.row_data', function(event) {
                event.preventDefault();

                if ($(this).attr('edit_type') == 'button') {
                    return false;
                }

                //make div editable
                $(this).closest('div').attr('contenteditable', 'true');
                //add bg css
                $(this).addClass('bg-warning').css('padding', '5px');

                $(this).focus();
            })
            //--->make div editable > end


            //--->save single field data > start
            $(document).on('focusout', '.row_data', function(event) {
                event.preventDefault();

                if ($(this).attr('edit_type') == 'button') {
                    return false;
                }

                var row_id = $(this).closest('tr').attr('row_id');

                var row_div = $(this)
                    .removeClass('bg-warning') //add bg css
                    .css('padding', '')

                var col_name = row_div.attr('col_name');
                var col_val = row_div.html();

                var arr = {};
                arr[col_name] = col_val;

                //use the "arr" object for your ajax call
                $.extend(arr, {
                    row_id: row_id
                });

                //out put to show
                console.log(JSON.stringify(arr, null, 2));


            })
            //--->save single field data > end


            //--->button > edit > start



            //--->button > cancel > start

            //--->button > cancel > end


            //--->save whole row entery > start
            $(document).on('click', '.btn_save', function(event) {
                event.preventDefault();
                var tbl_row = $(this).closest('tr');

                var row_id = tbl_row.attr('row_id');


                //hide save and cacel buttons



                //make the whole row editable
                tbl_row.find('.row_data')
                    .attr('edit_type', 'click')
                    .removeClass('bg-warning')
                    .css('padding', '')

                //--->get row data > start
                var arr = {};
                tbl_row.find('.row_data').each(function(index, val) {
                    var col_name = $(this).attr('col_name');
                    var col_val = $(this).html();
                    arr[col_name] = col_val;
                });
                //--->get row data > end

                //use the "arr" object for your ajax call
                $.extend(arr, {
                    row_id: row_id
                });

                //out put to show

                console.log(JSON.stringify(arr, null, 2));

                // update witness
                $.ajax({
                    url: '/ajax/witnesses/',
                    // url: '{% url "graphs:check_ajax_task" task_id=task_id%}',
                    data: arr,
                    dataType: 'json',
                    headers: {
                        'X-CSRFToken': csrftoken
                    }

                });
                // update witness > end
            });
            //--->save whole row entery > end
            //--->courtdates > begin
            const court_dates_json = JSON.parse(document.getElementById('court_dates_json').textContent)
            console.log(court_dates_json[0]);
            //--->create data table > start
            var tbl2 = '';
            tbl2 += '<table class="table table-hover table-condensed table-responsive table-striped" id="court_dates_table">'

            //--->create table header > start
            tbl2 += '<thead>';
            tbl2 += '<tr>';
            tbl2 += '<th>Date</th>';
            tbl2 += '<th>Progress</th>';
            tbl2 += '<th>Next Date </th>';
            tbl2 += '<th>Next Date For</th>';
            tbl2 += '<th>Options</th>';
            tbl2 += '</tr>';
            tbl2 += '</thead>';
            //--->create table header > end


            //--->create table body > start
            tbl2 += '<tbody>';

            //--->create table body rows > start
            $.each(court_dates_json, function(index, val) {
                //loop through ajax row data
                var row_id = val['uuid'];
                tbl2 += '<tr row_id="' + row_id + '">';
                tbl2 += '<td ><div class="row_data" edit_type="click" data_type = "date" col_name="hearing_date">' + val['hearing_date'] + '</div></td>';
                tbl2 += '<td ><div class="row_data" edit_type="click" col_name="comment">' + val['comment'] + '</div></td>';
                tbl2 += '<td ><div class="row_data" edit_type="click" data_type = "date"col_name="next_date">' + val['next_date'] + '</div></td>';
                tbl2 += '<td ><div class="row_data" edit_type="click" col_name="next_date_for_comment">' + val['next_date_for_comment'] + '</div></td>';
                //--->edit options > start
                tbl2 += '<td>';



                //only show this button if edit button is clicked
                tbl2 += '<span class="btn_save2"><a href="#" class="btn btn-link"  row_id="' + row_id + '">Save</a></span>';


                tbl2 += '</td>';
                //--->edit options > end

                tbl2 += '</tr>';
            });

            //--->create table body rows > end

            tbl2 += '</tbody>';
            //--->create table body > end

            tbl2 += '</table>'
            //--->create data table > end

            //out put table data
            $(document).find('.tbl_court_dates').html(tbl2);



            //--->make div editable > start
            $(document).on('click', '.row_data', function(event) {
                event.preventDefault();

                if ($(this).attr('edit_type') == 'button') {
                    return false;
                }

                //make div editable
                $(this).closest('div').attr('contenteditable', 'true');
                if ($(this).closest('div').attr('data_type') == 'date') {
                    $(this).datepicker({
                        dateFormat: "yy/mm/dd",
                        onSelect: function(dateText, inst) {
                            var date = $(this).val();
                            buffer = date;
                            $(this)[0].innerHTML = date;

                        }
                    });
                }

                //add bg css
                $(this).addClass('bg-warning').css('padding', '5px');

                $(this).focus();
            })
            //--->make div editable > end


            //--->save single field data > start
            $(document).on('focusout', '.row_data', function(event) {
                event.preventDefault();

                if ($(this).attr('edit_type') == 'button') {
                    return false;
                }
                if ($(this).closest('div').attr('data_type') == 'date') {
                    $(this).datepicker("destroy");
                    $(this)[0].innerHTML = buffer;
                }
                var row_id = $(this).closest('tr').attr('row_id');

                var row_div = $(this)
                    .removeClass('bg-warning') //add bg css
                    .css('padding', '')

                var col_name = row_div.attr('col_name');
                var col_val = row_div.html();

                var arr = {};
                arr[col_name] = col_val;

                //use the "arr" object for your ajax call
                $.extend(arr, {
                    row_id: row_id
                });

                //out put to show
                // $('.post_msg_court_date').html( '<pre class="bg-success">'+JSON.stringify(arr, null, 2) +'</pre>');

            })
            //--->save single field data > end


            //--->button > edit > start

            //--->button > edit > end


            //--->button > cancel > start

            //--->button > cancel > end


            //--->save whole row entery > start
            $(document).on('click', '.btn_save2', function(event) {
                event.preventDefault();
                var tbl_row = $(this).closest('tr');

                var row_id = tbl_row.attr('row_id');




                //make the whole row editable
                tbl_row.find('.row_data')
                    .attr('edit_type', 'click')
                    .removeClass('bg-warning')
                    .css('padding', '')

                //--->get row data > start
                var arr = {};
                tbl_row.find('.row_data').each(function(index, val) {
                    var col_name = $(this).attr('col_name');
                    var col_val = $(this).html();
                    arr[col_name] = col_val;
                });
                //--->get row data > end

                //use the "arr" object for your ajax call
                $.extend(arr, {
                    row_id: row_id
                });
                $.extend(arr, {
                    crime_uuid: window.location.pathname.split("/")[3]
                })
                //out put to show
                console.log(JSON.stringify(arr, null, 2));
                // update or add court date
                $(this).disabled = true;
                $.ajax({
                    url: '/ajax/court_dates/',
                    // url: '{% url "graphs:check_ajax_task" task_id=task_id%}',
                    data: arr,
                    dataType: 'json',
                    headers: {
                        'X-CSRFToken': csrftoken
                    },
                    success: function(data) {
                        $(this).disabled = false;

                    }

                });


            });
            $(document).on('click', '#add_court_date', function(e) {
                row_id = "new_row"

                var table = document.getElementById("court_dates_table");
                var row = table.insertRow(-1);

                // Insert new cells (<td> elements) at the 1st and 2nd position of the "new" <tr> element:
                var cell1 = row.insertCell(0);
                var cell2 = row.insertCell(1);
                var cell3 = row.insertCell(2);
                var cell4 = row.insertCell(3);
                var cell5 = row.insertCell(4);
                // Add some text to the new cells:
                cell1.innerHTML = '<div class="row_data" edit_type="click" data_type = "date" col_name="hearing_date">' + 'enter' + '</div>';
                cell2.innerHTML = '<div class="row_data" edit_type="click" col_name="comment">' + 'enter' + '</div>';
                cell3.innerHTML = '<div class="row_data" edit_type="click" data_type = "date" col_name="next_date">' + 'enter' + '</div>';
                cell4.innerHTML = '<div class="row_data" edit_type="click" col_name="next_date_for_comment">' + 'enter' + '</div>';
                //--->edit options > start
                cell5.innerHTML = '<span class="btn_save2"> <a href="#" class="btn btn-link"  row_id="' + row_id + '">Save</a></span>'



            });
        }
    }
});
