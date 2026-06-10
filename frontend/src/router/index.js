import { createRouter, createWebHistory } from 'vue-router'
import ViewLogin from '../components/views/ViewLogin.vue'
import ViewDashboard from '../components/views/ViewDashboard.vue'
import ViewTeacher from '../components/views/ViewTeacher.vue'
import ViewStudent from '../components/views/ViewStudent.vue'
import ViewGrading from '../components/views/ViewGrading.vue'
import ViewAnalytics from '../components/views/ViewAnalytics.vue'
import ViewGrades from '../components/views/ViewGrades.vue'
import ViewTableManager from '../components/views/ViewTableManager.vue'
import ViewAccountManager from '../components/views/ViewAccountManager.vue'

const routes = [
  { path: '/', name: 'Login', component: ViewLogin },
  { path: '/dashboard', name: 'Dashboard', component: ViewDashboard },
  { path: '/teacher', name: 'Teacher', component: ViewTeacher },
  { path: '/student', name: 'Student', component: ViewStudent },
  { path: '/grading', name: 'Grading', component: ViewGrading },
  { path: '/analytics', name: 'Analytics', component: ViewAnalytics },
  { path: '/grades', name: 'Grades', component: ViewGrades },
  { path: '/table-manager', name: 'TableManager', component: ViewTableManager },
  { path: '/account-manager', name: 'AccountManager', component: ViewAccountManager },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ─── Navigation guard ───
router.beforeEach((to, from) => {
  const auth = JSON.parse(localStorage.getItem('ai_assistant_auth') || '{}')
  if (!auth.isLoggedIn && to.name !== 'Login') {
    return { name: 'Login' }
  }
  if (auth.isLoggedIn && to.name === 'Login') {
    const role = auth.role
    if (role === 'admin') return { name: 'AccountManager' }
    if (role === 'student') return { name: 'Student' }
    return { name: 'Dashboard' }
  }
})

export default router