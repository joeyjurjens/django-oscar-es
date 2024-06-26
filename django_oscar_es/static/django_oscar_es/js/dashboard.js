$(document).ready(function() {
    $('select[name^="facets-"][name$="-facet_type"]').change(function() {
        const rangeOptionsTableContainer = $(this).closest('tr').next().find('#range-options-table-container');
        if ($(this).val() === 'range') {
            rangeOptionsTableContainer.show();
        } else {
            rangeOptionsTableContainer.hide();
        }
    });
    
    $('select[name^="facets-"][name$="-facet_type"]').trigger('change');

    $("#facet-tbody").sortable({
        items: ".sortable-row",
        cursor: "grabbing",
        handle: ".sortable-handle",
        start: function(event, ui) {
            $("tr[data-nested-for='" + ui.item.attr('id') + "']").hide();
        },
        stop: function(event, ui) {
            $("tr[data-nested-for='" + ui.item.attr('id') + "']").detach().insertAfter(ui.item).show();
        },
        update: function(event, ui) {
            updateFacetOrdering();
        }
    });

    function updateFacetOrdering() {
        $('#facet-tbody .sortable-row').each(function(index) {
            $(this).find('input[name$="-order"]').val(index);
        });
    }
});
