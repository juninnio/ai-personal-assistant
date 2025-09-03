// components/ui/Input.jsx
import React from 'react';

const Input = ({
  label,
  type = 'text',
  name,
  value,
  onChange,
  placeholder,
  required = false,
  disabled = false,
  error,
  className = '',
  ...props
}) => {
  const inputId = `input-${name}`;
  
  // Base input styles
  const baseStyles = 'w-full px-3 py-2 border rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0';
  
  // Conditional styles based on state
  const stateStyles = error 
    ? 'border-red-300 focus:border-red-500 focus:ring-red-200' 
    : 'border-gray-300 focus:border-blue-500 focus:ring-blue-200';
  
  const disabledStyles = disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white';
  
  const inputStyles = `${baseStyles} ${stateStyles} ${disabledStyles} ${className}`;

  return (
    <div className="space-y-1">
      {label && (
        <label 
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <input
        id={inputId}
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        className={inputStyles}
        {...props}
      />
      
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

export default Input;