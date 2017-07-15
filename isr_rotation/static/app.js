(function($){

    var UserManager = (function(){

        function _applyUserStatus (){

            $('.user-list').find('.badge').remove();
            $('.user-list').removeClass('disabled');

            $.get('/api/get-status', function(data){
                data.users.forEach(function(u){
                    var elem = 'li[data-userid=' + u.user_id + ']';

                    if(u.is_current){
                        $(elem).append('<span class="badge" style="margin-right:6px;">Current</span>');
                    } else if (u.is_next) {
                        $(elem).append('<span class="badge" style="margin-right:6px;">Next</span>');
                    }

                    if (u.is_vacation){
                        $(elem).addClass('disabled');
                    }
                });
            });
        }

        return {
            applyStatus: _applyUserStatus
        };

    })();


    //
    //  Events
    //
    (function(UserManager){

        $(document).ready(function(){
            UserManager.applyStatus();
        });

        // Submit add new user
        $('#submitAddNewUser').click(function(){
            var str = $('#addNewUserForm').serialize();
            $.post('/api/add-user', str, function(){ location.reload(); });
        });

        // Submit delete user
        $('#submitDeleteUser').click(function(){
            var data = $('#deleteUserForm').serialize();
            $.post('/api/delete-user', data, function(){ location.reload(); });
        });

        // Submit update user
        $('#submitUpdateUser').click(function(){
            var data = $('#updateUserForm').serialize();
            $.post('/api/update-user', data, function(){ location.reload(); });

        });

        // Passing user ID to modal - Delete
        $('.btn-delete-user').click(function(){
            userId = $(this).data('userid');
            $('#deleteUserId').val(userId);
            $.get('/api/user/' + userId, function(data){
                $('#userNameEmail').html(data.name + ' / ' + data.email);
            });
        });

        // Passing user ID to modal - Update
        $('.btn-update-user').click(function(){
            userId = $(this).data('userid');
            $('#updateUserId').val(userId);
            $.get('/api/user/' + userId, function(data){
                $('#updateUserForm [name=email]').val(data.email);
                $('#updateUserForm [name=name]').val(data.name);
            });
        });

        // Resend
        $('#submitResend').click(function(){
            $.post('/api/resend', function(data){
                //console.log(data.status);
            });
        });

        // Move Next
        $('#submitMoveNext').click(function(){
            $.post('/api/move-next', function(data){
                //console.log(data.status);
            });

            UserManager.applyStatus();
        });

        // Save Sequences
        $('#BtnSave').click(function(){

            var onDuty = [];

            $('#onDutyTable li').each(function(index, val){
                console.log('On: User ID =>', $(val).data('userid'), 'Index =>', index);
                onDuty.push({
                    'userid': $(val).data('userid'),
                    'index': index
                });
            });

            var offDuty = [];

            $('#offDutyTable li').each(function(index, val){
                console.log('Off: User ID =>', $(val).data('userid'), 'Index =>', index);
                offDuty.push({
                    userid: $(val).data('userid'),
                    index: index
                });
            });

            $.ajax({
                url: '/api/set-user',
                dataType: 'json',
                contentType: 'application/json',
                method: 'POST',
                data: JSON.stringify({
                    onDuty: onDuty,
                    offDuty: offDuty
                })
            }).done(function(data){
               //console.log(data);
               UserManager.applyStatus();

               // Change button color
               if (data.status === 'ok'){
                    $('#BtnSave').switchClass('btn-primary', 'btn-success', 200, 'easeInOutQuad')
                                 .switchClass( 'btn-success','btn-primary', 800, 'easeInOutQuad');
               } else {
                    $('#BtnSave').switchClass('btn-primary', 'btn-danger', 200, 'easeInOutQuad')
                                 .switchClass( 'btn-danger','btn-primary', 800, 'easeInOutQuad');
               }
            });
        });

        // Update sequences
        $("#onDutyTable, #offDutyTable").sortable({
            connectWith: ".connectedSortable",
            dropOnEmpty: true
        }).disableSelection();

    })(UserManager);

    //
    //  Date Picker
    //
    (function(){

        // Set date picker
        var _from = $('#startVac').datepicker({
            changeMonth: true,
            numberOfMonth: 1,
        }).on('change', function(){
            _to.datepicker('option', 'minDate', getDate(this));
        });

        var _to = $('#endVac').datepicker({
            changeMonth: true,
            numberOfMonth: 1,
        }).on('change', function(){
            _from.datepicker('option', 'maxDate', getDate(this));
        });

        function getDate(element){
            var date;
            try {
                date = $.datepicker.parseDate('mm/dd/yy', element.value);
            } catch(ex) {
                date = null;
            }
            return date;
        }
    })();


})(jQuery);

