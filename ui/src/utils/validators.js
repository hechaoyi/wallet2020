import validate from 'validate.js';

const array = (arrayItems, itemConstraints) => {
  const arrayItemErrors = arrayItems.reduce((errors, item, index) => {
    const error = validate(item, itemConstraints, {fullMessages: false});
    if (error) errors[index] = error;
    return errors;
  }, {});
  return Object.entries(arrayItemErrors).length === 0 ? null : arrayItemErrors;
};

validate.validators = {...validate.validators, array};
