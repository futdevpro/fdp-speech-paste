# AI Development Guide

## Language Requirements
- Write all code in English
- Write all logs in English
- Write all code documentation in Hungarian
- Write all comments in Hungarian
- Write all error messages in English

## Core Rules
- Read and follow naming conventions (see [Naming Conventions](naming.md))
- Use explicit type definitions (avoid automatic type inference)
- Implement proper error handling
- Never write logics into getters, getters should be only mappers
- If the task is complex, or need includes many subject members, do it one by one

## Code Structure
- One class/function per file
- Clear file organization
- Consistent import order
- No circular dependencies
- Proper separation of concerns

## Error Handling
- Use try-catch blocks
- Log all errors in English
- Provide meaningful error messages in English
- Handle edge cases
- Validate inputs

## Testing Requirements
- Unit tests for all functions
- Integration tests for features
- Test edge cases
- Maintain test coverage
- Mock external dependencies

## Documentation
- Hungarian comments and documentation
- JSDoc for functions in Hungarian
- Clear parameter descriptions in Hungarian
- Usage examples in Hungarian
- Update docs with changes

## Best Practices
- DRY (Don't Repeat Yourself)
- SOLID principles
- Clean code practices
- Performance optimization
- Security considerations

## Project-Specific Guidelines
- Only for Frontend Development: Read [Frontend Guidelines](frontend.md)
- Only for Backend Development: Read [Backend Guidelines](backend.md) 

## Refactor
- All files length should be under 300 lines
  - For files over 300 lines, mark it with "// [TOO LONG FILE]"

## Format
- Break long lines, use lint project's rules