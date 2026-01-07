/**
 * Button Component
 */

import Spinner from './Spinner';

const Button = ({
    children,
    type = 'button',
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    className = '',
    onClick,
    ...props
}) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-300 focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const variants = {
        primary: 'bg-gradient-to-r from-primary-500 to-primary-600 text-white hover:from-primary-600 hover:to-primary-700 shadow-lg hover:shadow-primary-500/25 focus:ring-primary-500/50',
        secondary: 'bg-dark-800 border border-dark-600 text-dark-100 hover:bg-dark-700 hover:border-dark-500 focus:ring-dark-500/50',
        ghost: 'text-dark-300 hover:text-dark-100 hover:bg-dark-800/50 focus:ring-dark-500/50',
        danger: 'bg-gradient-to-r from-red-500 to-red-600 text-white hover:from-red-600 hover:to-red-700 shadow-lg hover:shadow-red-500/25 focus:ring-red-500/50',
    };

    const sizes = {
        sm: 'px-4 py-2 text-sm',
        md: 'px-6 py-3 text-base',
        lg: 'px-8 py-4 text-lg',
    };

    return (
        <button
            type={type}
            disabled={disabled || loading}
            onClick={onClick}
            className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
            {...props}
        >
            {loading && <Spinner size="sm" className="mr-2" />}
            {children}
        </button>
    );
};

export default Button;
