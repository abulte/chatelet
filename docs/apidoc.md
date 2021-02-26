# chatelet API
## Version: v1

### /api/subscriptions/

#### GET
##### Summary

List subscriptions

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |

##### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | List of subscriptions | [ [AddSubscriptionResponse](#addsubscriptionresponse) ] |

#### POST
##### Summary

Add a subscription

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| body | body |  | No | [AddSubscription](#addsubscription) |

##### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Subscription already exists | [AddSubscriptionResponse](#addsubscriptionresponse) |
| 201 | Subscription created | [AddSubscriptionResponse](#addsubscriptionresponse) |
| 403 | The url domain is not in accept list |  |
| 404 | Not found |  |
| 422 | Validation error |  |

### /api/publications/

#### POST
##### Summary

Publish an event

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| body | body |  | No | [AddPublication](#addpublication) |

##### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 201 | Publication created | [DispatchEvent](#dispatchevent) |
| 404 | Not found |  |
| 422 | Validation error |  |

### Models

#### AddSubscriptionResponse

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| id | integer |  | No |
| event | string |  | Yes |
| url | string (url) |  | Yes |
| event_filter | string |  | No |

#### AddSubscription

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| event | string |  | Yes |
| url | string (url) |  | Yes |
| event_filter | string |  | No |

#### AddPublication

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| event | string |  | Yes |
| payload | object |  | Yes |

#### DispatchEvent

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| subscription | integer |  | No |
| ok | boolean |  | No |
| event | string |  | Yes |
| payload | object |  | No |
