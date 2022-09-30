odoo.define('xks_crm.web_ir_actions_dialog_view', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var Dialog = require('web.Dialog');

    var core = require('web.core');
    var dialogs = require('web.view_dialogs');
    var Sidebar = require('web.Sidebar');

    var _t = core._t;
    var qweb = core.qweb;

    var clickDataAction = ''; // 用来保存触发按钮的data-actionState属性值

    FormController.include({
         //后续内容写在此处

    })

    //实现按钮不触发odoo 保存操作
    function saveAndExecuteAction() {
        //（说明）在原方法上新增的部分    保存从dom上获取的data属性
        var evData = clickDataAction = ev.data.attrs['data-actionState']
        // 根据值类型，判断后续的逻辑
        if (evData && evData === 'm-noSave') { // 如果为"m-noSave", 则不进行后续的保存和验证
        var record = self.model.get(ev.data.record.id);
            // 直接调用按钮对应的方法
            return self._callButtonAction(attrs, record);
        } else {
            // 原逻辑
            return self.saveRecord(self.handle, {
                stayInEdit: true,
            }).then(function () {
                var record = self.model.get(ev.data.record.id);
                return self._callButtonAction(attrs, record);
            });
        }
    }

    // xml中按钮为
    // <button name="cancel" type="object" string="取消" data-actionState="m-cancel"/>
    // 实现取消按钮功能，点击按钮后关闭页面
    // if (evData && evData === 'm-cancel') { // 取消按钮
    //     var record = self.model.get(ev.data.record.id);
    //     self._discardChanges(); // 关闭视图
    //     return self._callButtonAction(attrs, record);
    // }

    // 切换视图只读或者编辑模式
    // if (evData && evData === 'm-toggle-mode') { // 如果为切换视图状态
    //     var isEdit = self.mode === 'edit'; // 判断是否为编辑状态
    //     self._setMode(isEdit ? 'readonly' : 'edit') // 设置视图类型
    //     self.initialState.context['form_state'] = isEdit ? 'readonly' : 'edit'
    //     return self._callButtonAction(attrs, record); // 返回按钮事件（目前看，是必须要返回的）
    // }

    // 只读模式隐藏 m-form-view-hidden
    // <button name="go_to_list" class="m-form-view-hidden" type="object" string="取消" data-actionState="m-noSave"/>
    // 编辑模式隐藏 m-form-edit-hidden
    // <button name="go_to_list" class="m-form-edit-hidden" type="object" string="返回" data-actionState="m-noSave"/>
    // 根据form视图模式显示或者隐藏按钮
    // 更新按钮状态
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

            // 需要等到dom加载完在执行逻辑
            $(document).ready(() => {
                // 新增条件，用来切换自定义按钮的显示和隐藏
                [].forEach.call(document.querySelectorAll('.m-form-edit-hidden'), element => {
                    $(element).toggleClass('o_hidden', edit_mode);
                });

                [].forEach.call($('.m-form-view-hidden'), element => {
                    $(element).toggleClass('o_hidden', !edit_mode);
                })
            });
        }
    }

    // <button name="save_contract" className="m-form-view-hidden" type="object" string="保存草稿" data-actionState="m-no-valid"/>
    // 实现保存但不验证功能
    function canBeSaved(recordID) {
        var fieldNames = this.renderer.canBeSaved(recordID || this.handle);
        // 新增属性判断，用来跳过验证，直接保存
        fieldNames.length = clickDataAction === 'm-no-valid' ? 0 : fieldNames.length
        if (fieldNames.length) {
            this._notifyInvalidFields(fieldNames);
            return false;
        }
        return true;
    }
})