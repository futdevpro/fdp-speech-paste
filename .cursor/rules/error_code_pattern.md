# Error Code Pattern [FDP-Dev-Error]

## Format
```
[PROJ]-[SERV]-[FUNC]
```

## Components
- PROJ: 3 character project code
  - FMP: FDP Master Prompter
  - CUR: Cursor
  - DYN: Dynamo
  - etc.
- SERV: 3-4 character service code (abbreviated from service name)
  - DTS: _DataService
  - CTR: _Controller
  - SSS: _SocketServerService
  - SCS: _SocketClientService
  - EMS: _EmailService
  - etc.
- FUNC: 3-4 character function code (derived from function name + index)
  - NC2: newChange (second throw)
  - GF1: getFile (first throw)
  - etc.

## Examples
- FMP-DTS-NC2: Second error in newChange function of TokenHistory_DataService
- FMP-CTR-GF1: First error in getFile function of User_Controller
- CUR-SSS-UP3: Third error in updateProfile function of Chat_SocketServerService
- DYN-SCS-EM1: First error in sendMessage function of Chat_SocketClientService
- FMP-EMS-NT1: First error in sendNotification function of Notification_EmailService
- ASD-SSS-ST0: The function's main try and catch rewrap error point.

## Usage
- Use in all backend error responses
- Include in error logs
- Reference in documentation
- Keep error codes consistent
- Document all error codes 
- All error codes should be unique in the entire system across all projects.