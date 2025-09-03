const API_BASE_URL = "http://localhost:8000"

const apiRequest = async (endpoint, options = {}) => {
    const token = localStorage.getItem('token');

    const config = {
        headers: {
            'Content-Type' : 'application/json',
            ...options.headers
        },
        ...options
    };

    if (token){
        config.headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    const data = await response.json();

    if (!response.ok) {
        if(response.status  === 401)  {
            localStorage.removeItem('token');
            localStorage.removeItem('username');
            localStorage.removeItem('user_id');
            throw new Error('Session expired. Please login again')
        }
        throw new Error(data.detail || 'Request Failes')
    }

    return data;
};

export const authServices = {
    register: async (userData) => {
        return apiRequest('/register',{
            method:'POST',
            body: JSON.stringify(userData),
        });
    },

    login: async(credentials) =>{
        const response = await apiRequest('/login',{
            method: 'POST',
            body: JSON.stringify(credentials),
        });

        localStorage.setItem('token', response.access_token);
        localStorage.setItem('username', response.username);
        localStorage.setItem('user_id', response.user_id);

        return response
    },

    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        localStorage.removeItem('user_id');
    },

    isAuthenticated : ()=>{
        return !!localStorage.getItem('token')
    },

    getCurrentUser: () => {
        const token = localStorage.getItem('token');
        const username = localStorage.getItem('username');
        const user_id = localStorage.getItem('user_id');

        if (!token) return null;

        return {
            token,
            username,
            userId : parseInt(user_id)
        };
    },

    getGoogleAuthUrl: async () => {
        return apiRequest('/auth/google');
    },

    getGoogleStatus: async() => {
        return apiRequest('/google/status');
    },

    unlinkGoogle: async() => {
        return apiRequest('/auth/google/unlink', {method: "DELETE"});
    }
}