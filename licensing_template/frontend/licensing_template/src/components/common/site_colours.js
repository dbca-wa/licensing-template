import {Circle as CircleStyle, Fill, Stroke, Style, Icon} from 'ol/style';

export const SiteColours = {
    'draft': {
        'fill': '#e0e0e0',
        'stroke': '#616161',
    },
    'draft_external': {
        'fill': '#ffdd44',
        'stroke': '#ffcc33',
    },
    'pending': {
        'fill': '#0070FF',
        'stroke': '#000000',
    },
    'current': {
        'fill': '#00ff00', 
        'stroke': '#000000',
    },
    'approved': {
        'fill': '#0070ff', 
        'stroke': '#000000',
    },
    'suspended': {
        'fill': '#ffffff',
        'stroke': '#000000',
    },
    'not_to_be_reissued': {
        'fill': '#ff0000',
        'stroke': '#000000',
    },
    'denied': {
        'fill': '#000000',
        'stroke': '#000000',
        'icon_colour': '#000000',
    },
    'vacant': {
        'fill': '#ffaa00',
        'stroke': '#000000'
    },
    'pending_vacant': {
        'fill': '#ffaa00',
        'stroke': '#0077FF'
    },
    'transferred': {
        'fill': '#888888',
        'stroke': '#000000',
    },
    'dpaw_pool_of_sites': {
        'fill': '#a900e6',
        'stroke': '#000000',
        'icon_colour': '#a900e6',
    },
    'making_payment': {
        'fill': '#40e0d0',
        'stroke': '#000000'
    },
    'discarded': {
        'fill': '#ffe0d0',
        'stroke': '#ff0000'
    },
    'default': {
        'fill': '#40e0d0',
        'stroke': '#000000'
    }
}
export default SiteColours
export let existingSiteRadius = 5
export let drawingSiteRadius = 7
export function getStatusForColour(feature_or_apiary_site, vacant_suppress_discard = true, display_at_time_of_submitted = false){
    let status = ''
    let is_vacant = false
    let is_vacant_when_submitted = false
    let making_payment = false

    if (feature_or_apiary_site.hasOwnProperty('ol_uid')){
        // feature_or_apiary_site is Feature object
        status = feature_or_apiary_site.get("status");
        is_vacant = feature_or_apiary_site.get('is_vacant')
        making_payment = feature_or_apiary_site.get('making_payment')
        is_vacant_when_submitted = feature_or_apiary_site.get('apiary_site_is_vacant_when_submitted')
    } else {
        // feature_or_apiary_site is apiary_site object
        status = feature_or_apiary_site.properties.status
        is_vacant = feature_or_apiary_site.properties.is_vacant
        making_payment = feature_or_apiary_site.properties.making_payment
        is_vacant_when_submitted = feature_or_apiary_site.properties.apiary_site_is_vacant_when_submitted
    }

    if (display_at_time_of_submitted){
        status = 'pending'
        if (is_vacant_when_submitted){
            status = 'vacant'
        }
    } else {
        if (making_payment){
            status = 'making_payment'
        } else {
            if (is_vacant){
                // Vacant
                if (status == 'pending'){
                    status = 'pending_vacant'
                } else {
                    if (!vacant_suppress_discard && status == 'discarded'){
                        // When the site is 'vacant' and 'discarded', status remains the 'discarded'
                    } else {
                        // Set 'vacant' to the site status
                        status = 'vacant'
                    }
                }
            }
        }
    }

    return status
}
export function getApiaryFeatureStyle(status, selected=false, stroke_width_when_selected=2){
    let additional_width = selected ? stroke_width_when_selected : 0
    switch(status){
        case 'draft':
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.draft.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.draft.stroke,
                        width: 1 + additional_width
                    })
                })
            });
            break;
        case 'pending':
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.pending.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.pending.stroke,
                        width: 1 + additional_width
                    })
                })
            });
            break;
        case 'current':
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.current.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.current.stroke,
                        width: 1 + additional_width
                    })
                })
            });
            break;
        case 'approved':
            // Apiary site can be 'approved' status on a proposal
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.current.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.current.stroke,
                        width: 1 + additional_width
                    })
                })
            });
            break;
        case 'suspended':
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.suspended.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.suspended.stroke,
                        width: 1 + additional_width
                    })
                })
            });
            break;
        case 'not_to_be_reissued':
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.not_to_be_reissued.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.not_to_be_reissued.stroke,
                        width: 1 + additional_width
                    })
                })
            });
            break;
        case 'denied':
            return new Style({
                image: new Icon({
                    color: SiteColours.denied.icon_colour,
                    //src: "data/x2.png"
                    src: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgAADsIBFShKgAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4xMzQDW3oAAACMSURBVChTlZDbDYAwDAM7AAOw/ypISEyAEMOUXHDS8viAk0xDYkPbUmv9pShgMg3lBj3NIAOrv95C1OoBngyMaoCHpN6M5wzoa31olsDN8rQAMDBtpoDazWD1I8A2FlNA3Z+pBRiYYs+7BHkRtp4PGhpAHPDtIjJwMfsvDWr1AE8G4GIO6GkGGfioWg6CRJYCwPQeRwAAAABJRU5ErkJggg=="
                })
            });
            break;
        case 'transferred':
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.transferred.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.transferred.stroke,
                        width: 1 + additional_width
                    })
                })
            });
            break;
        case 'discarded':
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.discarded.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.discarded.stroke,
                        width: 1 + additional_width
                    })
                })
            });
            break;
        case 'vacant':
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.vacant.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.vacant.stroke,
                        width: 1 + additional_width
                    })
                })
            });
            break;
        case 'pending_vacant':
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.pending_vacant.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.pending_vacant.stroke,
                        width: 1 + additional_width
                    })
                })
            });
            break;
        case 'dpaw_pool_of_sites':
            return new Style({
                image: new Icon({
                color: SiteColours.dpaw_pool_of_sites.icon_colour,
                    //src: "data/+2.png"
                    src: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAZdEVYdFNvZnR3YXJlAHBhaW50Lm5ldCA0LjAuMTM0A1t6AAAAQklEQVQoU52LMQoAIBDD/P+n69KAmBvEQJaGriSToKahgpqGCmoaKqhpqKB2xie+DpOgpqGCmoYKahoqqGmocO1ZGzz92jSqmlDHAAAAAElFTkSuQmCC"
                }),
            });
            break;
        case 'making_payment':
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.making_payment.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.making_payment.stroke,
                        width: 1 + additional_width
                    })
                })
            });
            break;
        default:
            return new Style({
                image: new CircleStyle({
                    radius: existingSiteRadius,
                    fill: new Fill({
                        color: SiteColours.default.fill
                    }),
                    stroke: new Stroke({
                        color: SiteColours.default.stroke,
                        width: 2 + additional_width
                    })
                })
            });
            break;
    }
}
export function getDisplayNameOfCategory(key) {
    switch(key){
        case 'south_west':
            return 'South West'
            break
        case 'remote':
            return 'Remote'
            break
        default:
            return ''
            break
    }
}
export function getDisplayNameFromStatus(status_name){
    switch(status_name){
        case 'draft':
            return 'Draft'
            break
        case 'pending':
            return 'Pending'
            break
        case 'approved':
            return 'Approved'
            break
        case 'denied':
            return 'Denied'
            break
        case 'current':
            return 'Current'
            break
        case 'not_to_be_reissued':
            return 'Not to be re-issued'
            break
        case 'suspended':
            return 'Suspended'
            break
        case 'transferred':
            return 'Transferred'
            break
        case 'vacant':
            return 'Vacant'
            break
        case 'discarded':
            return 'Discarded'
            break
        default:
            if (status_name.toLowerCase().includes('vacant') && status_name.toLowerCase().includes('pending')){
                return 'Pending (vacant)'
            }
            return status_name
            break
    }
}
