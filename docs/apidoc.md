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
| 404 | Event not found |  |
| 422 | Validation error |  |

### /api/subscriptions/{id}/activate/

#### POST
##### Summary

Validate intent of a subscription

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| x-hook-secret | header |  | No |  |
| id | path |  | Yes | string |

##### Responses

| Code | Description |
| ---- | ----------- |
| 200 | Subscription validated |
| 404 | Not found |
| 422 | Validation error |

### /api/publications/

#### POST
##### Summary

Publish an event

##### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ---- |
| body | body |  | No | [AddPublication](#addpublication) |
| x-hook-signature | header |  | No |  |

##### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 201 | Publication created | [DispatchEvent](#dispatchevent) |
| 401 |  |  |
| 404 | Event not found |  |
| 422 | Validation error |  |

### Models

#### AddSubscriptionResponse

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| url | string (url) |  | Yes |
| event_filter | string |  | No |
| id | integer |  | No |
| active | boolean |  | No |
| event | string |  | Yes |

#### AddSubscription

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| url | string (url) |  | Yes |
| event_filter | string |  | No |
| event | string |  | Yes |

#### AddPublication

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| payload | object |  | Yes |
| event | string |  | Yes |

#### DispatchEvent

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| ok | boolean |  | No |
| payload | object |  | No |
| subscription | integer |  | No |
| event | string |  | Yes |
