/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {CharField, charField} from "@web/views/fields/char/char_field";
import {markup, useState} from "@odoo/owl";


export class MapViewer extends CharField {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.page = 1;
        this.state = useState({
            isValid: true,
        });
    }

    get url() {
        let url;
        if (this.props.record.data[this.props.name]) {
            url = markup(this.props.record.data[this.props.name]);
        }
        return url || this.props.value;
    }

}

MapViewer.template = "geo_iworks.GoogleMapViewer";

export const googleMapsViewer = {
    ...charField,
    component: MapViewer,
    displayName: _t("Google Maps Viewer"),
};

registry.category("fields").add("embed_map_viewer", googleMapsViewer);
