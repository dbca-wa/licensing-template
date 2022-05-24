<template>
    <div class="row col-sm-12">
        <template v-if="question.accessing_user_can_view">
            <div class="row form-group">
                <div class="col-md-3">
                    <label for="">{{ question.checklist_question.text }}</label>
                </div>
                <div class="col-md-9">
                    <template v-if="question.checklist_question.answer_type=='free_text'">
                        <textarea class="form-control free_text_area" :id="'free_text_' + question.id" v-model="question.answer_text" :disabled="!question.accessing_user_can_answer"/>
                    </template>
                    <template v-else>
                        <div>
                            <input type="radio" :id="'answer_yes_' + question.id" value="true" v-model="question.answer_yes_no" :disabled="!question.accessing_user_can_answer">
                            <label :for="'answer_yes_' + question.id">Yes</label>
                        </div>
                        <div>
                            <input type="radio" :id="'answer_no_' + question.id" value="false" v-model="question.answer_yes_no" :disabled="!question.accessing_user_can_answer">
                            <label :for="'answer_no_' + question.id">No</label>
                        </div>
                    </template>
                </div>
            </div>
        </template>
    </div>
</template>

<script>
import { api_endpoints, helpers, constants } from '@/utils/hooks'

export default {
    name: 'ChecklistQuestion',
    data: function() {
        let vm = this;
        return {

        }
    },
    props: {
        question: {
            type: Object,
            default: null,
        },
    }
}
</script>

<style scoped>
.free_text_area {
    resize: vertical;
}
</style>
