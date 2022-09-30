odoo.define('xks_crm.web_ir_actions_dialog_view', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var Dialog = require('web.Dialog');

    var core = require('web.core');
    var dialogs = require('web.view_dialogs');
    var Sidebar = require('web.Sidebar');

    var _t = core._t;
    var qweb = core.qweb;

    var clickDataAction = ''; // �������津����ť��data-actionState����ֵ

    FormController.include({
         //��������д�ڴ˴�

    })

    //ʵ�ְ�ť������odoo �������
    function saveAndExecuteAction() {
        //��˵������ԭ�����������Ĳ���    �����dom�ϻ�ȡ��data����
        var evData = clickDataAction = ev.data.attrs['data-actionState']
        // ����ֵ���ͣ��жϺ������߼�
        if (evData && evData === 'm-noSave') { // ���Ϊ"m-noSave", �򲻽��к����ı������֤
        var record = self.model.get(ev.data.record.id);
            // ֱ�ӵ��ð�ť��Ӧ�ķ���
            return self._callButtonAction(attrs, record);
        } else {
            // ԭ�߼�
            return self.saveRecord(self.handle, {
                stayInEdit: true,
            }).then(function () {
                var record = self.model.get(ev.data.record.id);
                return self._callButtonAction(attrs, record);
            });
        }
    }

    // xml�а�ťΪ
    // <button name="cancel" type="object" string="ȡ��" data-actionState="m-cancel"/>
    // ʵ��ȡ����ť���ܣ������ť��ر�ҳ��
    // if (evData && evData === 'm-cancel') { // ȡ����ť
    //     var record = self.model.get(ev.data.record.id);
    //     self._discardChanges(); // �ر���ͼ
    //     return self._callButtonAction(attrs, record);
    // }

    // �л���ͼֻ�����߱༭ģʽ
    // if (evData && evData === 'm-toggle-mode') { // ���Ϊ�л���ͼ״̬
    //     var isEdit = self.mode === 'edit'; // �ж��Ƿ�Ϊ�༭״̬
    //     self._setMode(isEdit ? 'readonly' : 'edit') // ������ͼ����
    //     self.initialState.context['form_state'] = isEdit ? 'readonly' : 'edit'
    //     return self._callButtonAction(attrs, record); // ���ذ�ť�¼���Ŀǰ�����Ǳ���Ҫ���صģ�
    // }

    // ֻ��ģʽ���� m-form-view-hidden
    // <button name="go_to_list" class="m-form-view-hidden" type="object" string="ȡ��" data-actionState="m-noSave"/>
    // �༭ģʽ���� m-form-edit-hidden
    // <button name="go_to_list" class="m-form-edit-hidden" type="object" string="����" data-actionState="m-noSave"/>
    // ����form��ͼģʽ��ʾ�������ذ�ť
    // ���°�ť״̬
    function _updateButtons () {
        if (this.$buttons) {
            if (this.footerToButtons) {
                var $footer = this.renderer.$('footer');
                if ($footer.length) {
                    this.$buttons.empty().append($footer);
                }
            }
            var edit_mode = (this.mode === 'edit');
            this.$buttons.find('.o_form_buttons_edit').toggleClass('o_hidden', !edit_mode);
            this.$buttons.find('.o_form_buttons_view') .toggleClass('o_hidden', edit_mode);

            // ��Ҫ�ȵ�dom��������ִ���߼�
            $(document).ready(() => {
                // ���������������л��Զ��尴ť����ʾ������
                [].forEach.call(document.querySelectorAll('.m-form-edit-hidden'), element => {
                    $(element).toggleClass('o_hidden', edit_mode);
                });

                [].forEach.call($('.m-form-view-hidden'), element => {
                    $(element).toggleClass('o_hidden', !edit_mode);
                })
            });
        }
    }

    // <button name="save_contract" className="m-form-view-hidden" type="object" string="����ݸ�" data-actionState="m-no-valid"/>
    // ʵ�ֱ��浫����֤����
    function canBeSaved(recordID) {
        var fieldNames = this.renderer.canBeSaved(recordID || this.handle);
        // ���������жϣ�����������֤��ֱ�ӱ���
        fieldNames.length = clickDataAction === 'm-no-valid' ? 0 : fieldNames.length
        if (fieldNames.length) {
            this._notifyInvalidFields(fieldNames);
            return false;
        }
        return true;
    }
})