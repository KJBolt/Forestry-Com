/** @odoo-module **/

import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {Component, onWillStart, onMounted, useState,} from "@odoo/owl";
import {useRecordObserver} from "@web/model/relational_model/utils";

export class FormulaEditor extends Component {
    static template = "sot_mrp_formula_builder.FormulaEditor";

    static props = {
        ...standardFieldProps,
        output_field_name: {type: String, optional: true},
        dynamic_variable_field_name: {type: String, optional: true},
    }

    setup() {
        this.orm = useService("orm");
        this.busService = this.env.services.bus_service;

        this.state = useState({
            showDropdown: false,
            formattedResult: this.props.record.data[this.props.name] || "",
            formulaValue: "",
            formula: "",
        });

        onWillStart(this.willStart);
        useRecordObserver(this.willUpdateRecord.bind(this));
        onMounted(() => this.onViewMounted());
    }

    // Lifecycle
    async willStart() {
        if (this.editingRecord) {
            // for performance in list views, plans are not retrieved until they are required.
            // await this.fetchAllPlans();

        }
        this.setDefaultValues();
    }

    setDefaultValues() {
        const html = this.formulaValue();
        // $('#dynamic-input').html(html);
    }

    async willUpdateRecord(record) {
        // Unless force_applicability, Plans need to be retrieved again as the product or account might have changed
        // and thus different applicabilities apply
        // or a model applies that contains unavailable plans
        // This should only execute when these fields have changed, therefore we use the `_field` props.
        this.formattedResult = record.data[this.props.name];

        // move cursor to the end of the text
        const currentVariable = record.data['variable_id'] || false;
        const currentFunction = record.data['function_id'] || false;
        if (currentVariable || currentFunction) {
            $('#dynamic-input').html(this.formattedResult);
            this.props.record.update({['variable_id']: false});
            this.props.record.update({['function_id']: false});
        }
    }

    onViewMounted() {
        const html = this.formulaValue();
        $('#dynamic-input').html(html);
    }

    get allowSave() {
        // check if the user has entered all formula values
        // for (const [key, value] of Object.entries(this.allVariables.variables)) {
        //     if (!this.allVariableValues[key]) {
        //         return false;
        //     }
        // }
        return true;
    }

    get editingRecord() {
        return !this.props.readonly;
    }

    onchangeInputDiv(event) {
        if (event.target) {
            this.state.formulaValue = event.target.innerHTML;
            this.state.formula = event.target.innerText;
        }

        this.save();
    }

    save() {
        if (this.allowSave) {
            const allDynamicVariables = $('#dynamic-input').find('.variable-span');
            const self = this;
            const variables = {
                'variables': [],
                'functions': [],
            };
            for (let i = 0; i < allDynamicVariables.length; i++) {
                const variable = $(allDynamicVariables[i]);
                const variableId = variable.data('id');
                const variableType = variable.data('type');

                if (variables[variableType].indexOf(variableId) === -1) {
                    variables[variableType].push(variableId)
                }
            }

            this.props.record.update({[this.props.output_field_name]: this.state.formula});
            this.props.record.update({[this.props.dynamic_variable_field_name]: variables});
            this.props.record.update({[this.props.name]: this.state.formulaValue});
        }
    }

    formulaValue() {
        return this.props.record.data[this.props.name];
    }

    closeFormulaValueEditor() {
        this.save();
    }

}

export const formulaEditor = {
    component: FormulaEditor,
    supportedTypes: ["char", "text"],
    fieldDependencies: [{name: "variable_id", type: "number"}, {name: "function_id", type: "number"}],
    supportedOptions: [
        {
            label: _t("Output Formula"),
            name: "output_field_name",
            type: "string",
        },
        {
            label: _t("Dynamic Values Json Field"),
            name: "dynamic_variable_field_name",
            type: "string",
        },
    ],
    extractProps: ({attrs, options}) => ({
        output_field_name: options.output_field_name,
        dynamic_variable_field_name: options.dynamic_variable_field_name,
    }),
};

registry.category("fields").add("formula_editor", formulaEditor);
